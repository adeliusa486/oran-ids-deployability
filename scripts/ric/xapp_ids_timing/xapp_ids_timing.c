/*
 * EXP-061: decision latency of the radio-layer detector through a live
 * FlexRIC near-RT RIC (v2.0.0), emulated E2 node, one host.
 *
 * Path per KPM indication:
 *   E2 node builds the indication (collectStartTime) -> E2AP/SCTP -> nearRT-RIC
 *   -> E42/SCTP -> this xApp (callback: arrival stamped, pushed to a queue)
 *   -> worker thread: per UE, 16-record window aggregation + ONNX Runtime
 *   -> one RC control (Radio Bearer Control, QoS flow mapping) -> RIC -> E2 node
 *   -> CONTROL-ACK back to the xApp.
 *
 * Timed terms (one CSV row per indication):
 *   t_ind   collectStartTime to callback entry, CLOCK_REALTIME, same host
 *           (agent encoding, SCTP, RIC forwarding, xApp decoding). The KPM
 *           v2.03 header carries a 4-byte timestamp, so FlexRIC sends the low
 *           32 bits of the agent's microsecond clock; the difference is taken
 *           modulo 2^32 (valid for delays below about 71 minutes).
 *   t_q     callback entry to worker start (queueing), CLOCK_MONOTONIC
 *   t_feat  window aggregation, t_inf ONNX inference (first UE, and summed
 *           over all UEs in the indication)
 *   t_act   RC control build + send + CONTROL-ACK round trip
 *
 * The emulated node's KPM values are synthetic, so model inputs are replayed
 * from the held-out test windows (results/EXP-061/models/windows.f32). The
 * transport terms are measured on real E2AP messages carrying 16 measurement
 * items per UE. Before timing, every test window is scored and compared with
 * the Python ONNX Runtime scores (ref_<model>.f32).
 *
 * Configuration by environment: IDS_MODEL, IDS_WINDOWS, IDS_REF, IDS_PERIOD_MS,
 * IDS_N (indications recorded after warm-up), IDS_WARMUP, IDS_OUT (CSV path).
 * FlexRIC's own -c/-p arguments are passed through.
 */
#include "../../../../src/xApp/e42_xapp_api.h"
#include "../../../../src/sm/rc_sm/ie/ir/ran_param_struct.h"
#include "../../../../src/sm/rc_sm/ie/ir/ran_param_list.h"
#include "../../../../src/util/time_now_us.h"

#include <onnxruntime_c_api.h>

#include <assert.h>
#include <math.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#if !defined(KPM_V2_03) && !defined(KPM_V3_00)
#error "EXP-061 expects KPM v2.03 or v3.00 (format 4 action definition)"
#endif

#define REC 16
#define KPM 16
#define NF (2 * KPM)
#define QCAP 8192

/* ---------------------------------------------------------------- ONNX */

static const OrtApi* ort;
static OrtSession* sess;
static OrtMemoryInfo* mem;
static char* out_names[2];
static size_t n_out;
static size_t prob_idx;
static const char* in_names[1] = {"input"};

static void ck(OrtStatus* s)
{
  if (s != NULL) {
    fprintf(stderr, "ONNX Runtime: %s\n", ort->GetErrorMessage(s));
    exit(1);
  }
}

static void ort_init(const char* path)
{
  ort = OrtGetApiBase()->GetApi(ORT_API_VERSION);
  OrtEnv* env = NULL;
  ck(ort->CreateEnv(ORT_LOGGING_LEVEL_WARNING, "ids", &env));
  OrtSessionOptions* so = NULL;
  ck(ort->CreateSessionOptions(&so));
  ck(ort->SetIntraOpNumThreads(so, 1));
  ck(ort->SetInterOpNumThreads(so, 1));
  ck(ort->SetSessionGraphOptimizationLevel(so, ORT_ENABLE_ALL));
  ck(ort->CreateSession(env, path, so, &sess));
  ck(ort->CreateCpuMemoryInfo(OrtArenaAllocator, OrtMemTypeDefault, &mem));

  OrtAllocator* al = NULL;
  ck(ort->GetAllocatorWithDefaultOptions(&al));
  ck(ort->SessionGetOutputCount(sess, &n_out));
  assert(n_out >= 1 && n_out <= 2);
  prob_idx = n_out - 1;
  for (size_t i = 0; i < n_out; ++i) {
    ck(ort->SessionGetOutputName(sess, i, al, &out_names[i]));
    if (strcmp(out_names[i], "probabilities") == 0)
      prob_idx = i;
  }
}

/* Same as onnx_proba() in experiments/run_latency_v2.py: attack probability. */
static float infer(float const* x)
{
  int64_t shape[2] = {1, NF};
  OrtValue* in = NULL;
  ck(ort->CreateTensorWithDataAsOrtValue(mem, (void*)x, NF * sizeof(float), shape, 2,
                                         ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT, &in));
  OrtValue* outs[2] = {NULL, NULL};
  ck(ort->Run(sess, NULL, in_names, (const OrtValue* const*)&in, 1,
              (const char* const*)out_names, n_out, outs));
  OrtTensorTypeAndShapeInfo* info = NULL;
  size_t cnt = 0;
  ck(ort->GetTensorTypeAndShape(outs[prob_idx], &info));
  ck(ort->GetTensorShapeElementCount(info, &cnt));
  ort->ReleaseTensorTypeAndShapeInfo(info);
  float* p = NULL;
  ck(ort->GetTensorMutableData(outs[prob_idx], (void**)&p));
  float const score = cnt == 2 ? p[1] : p[0];
  for (size_t i = 0; i < n_out; ++i)
    ort->ReleaseValue(outs[i]);
  ort->ReleaseValue(in);
  return score;
}

/* ------------------------------------------------------ window features */

static float* windows;
static size_t n_win;

/* load_radio's features: per KPM, nan-mean and sample standard deviation
   (ddof = 1) over the 16 records, interleaved f1_mean, f1_std, ...; NaN -> 0. */
static void aggregate(float const* w, float* out)
{
  for (int j = 0; j < KPM; ++j) {
    double s = 0.0;
    int n = 0;
    for (int r = 0; r < REC; ++r) {
      double const v = w[r * KPM + j];
      if (!isnan(v)) { s += v; ++n; }
    }
    double const mu = n > 0 ? s / n : NAN;
    double ss = 0.0;
    for (int r = 0; r < REC; ++r) {
      double const v = w[r * KPM + j];
      if (!isnan(v)) ss += (v - mu) * (v - mu);
    }
    double const sd = n > 1 ? sqrt(ss / (n - 1)) : NAN;
    out[2 * j] = isnan(mu) ? 0.0f : (float)mu;
    out[2 * j + 1] = isnan(sd) ? 0.0f : (float)sd;
  }
}

static void* read_all(const char* path, size_t* bytes)
{
  FILE* f = fopen(path, "rb");
  if (f == NULL) { fprintf(stderr, "cannot open %s\n", path); exit(1); }
  fseek(f, 0, SEEK_END);
  long const sz = ftell(f);
  fseek(f, 0, SEEK_SET);
  void* buf = malloc(sz);
  assert(buf != NULL);
  if (fread(buf, 1, sz, f) != (size_t)sz) { fprintf(stderr, "short read %s\n", path); exit(1); }
  fclose(f);
  *bytes = (size_t)sz;
  return buf;
}

static double verify(const char* ref_path)
{
  size_t bytes = 0;
  float* ref = read_all(ref_path, &bytes);
  if (bytes / sizeof(float) != n_win) { fprintf(stderr, "reference size mismatch\n"); exit(1); }
  double worst = 0.0;
  float x[NF];
  for (size_t i = 0; i < n_win; ++i) {
    aggregate(windows + i * REC * KPM, x);
    double const d = fabs((double)infer(x) - (double)ref[i]);
    if (d > worst) worst = d;
  }
  free(ref);
  return worst;
}

/* -------------------------------------------------------------- timing */

static int64_t mono_ns(void)
{
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return (int64_t)t.tv_sec * 1000000000LL + t.tv_nsec;
}

typedef struct {
  uint64_t seq;
  int64_t start_us;
  int64_t recv_us;   /* holds t_ind in microseconds after the callback */
  int64_t recv_ns;
  size_t n_ue;
  bool has_ue;
  ue_id_e2sm_t ue;
} item_t;

typedef struct {
  uint64_t seq;
  size_t n_ue;
  size_t qlen;
  int64_t t_ind_us;
  double t_q, t_feat1, t_inf1, t_feat, t_inf, t_act;
} row_t;

static item_t q[QCAP];
static size_t q_head, q_len;
static uint64_t n_seen, n_dropped;
static bool stopping;
static pthread_mutex_t q_mtx = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t q_cv = PTHREAD_COND_INITIALIZER;

static row_t* rows;
static size_t n_rows, cap_rows;
static global_e2_node_id_t const* node;

static void sm_cb_kpm(sm_ag_if_rd_t const* rd)
{
  int64_t const recv_us = time_now_us();
  int64_t const recv_ns = mono_ns();
  assert(rd->type == INDICATION_MSG_AGENT_IF_ANS_V0);
  assert(rd->ind.type == KPM_STATS_V3_0);
  kpm_ind_data_t const* kpm = &rd->ind.kpm.ind;

  item_t it = {0};
  it.start_us = kpm->hdr.kpm_ric_ind_hdr_format_1.collectStartTime;
  it.recv_us = (int64_t)(uint32_t)((uint32_t)recv_us - (uint32_t)it.start_us);
  it.recv_ns = recv_ns;
  if (kpm->msg.type == FORMAT_3_INDICATION_MESSAGE) {
    it.n_ue = kpm->msg.frm_3.ue_meas_report_lst_len;
    if (it.n_ue > 0) {
      it.ue = cp_ue_id_e2sm(&kpm->msg.frm_3.meas_report_per_ue[0].ue_meas_report_lst);
      it.has_ue = true;
    }
  }

  pthread_mutex_lock(&q_mtx);
  it.seq = n_seen++;
  if (q_len == QCAP) {
    ++n_dropped;
    if (it.has_ue) free_ue_id_e2sm(&it.ue);
  } else {
    q[(q_head + q_len) % QCAP] = it;
    ++q_len;
    pthread_cond_signal(&q_cv);
  }
  pthread_mutex_unlock(&q_mtx);
}

/* ---------------------------------------------- RC control (as xapp_kpm_rc) */

static byte_array_t copy_str_to_ba(const char* str)
{
  size_t const sz = strlen(str);
  byte_array_t dst = {.len = sz};
  dst.buf = calloc(sz, sizeof(uint8_t));
  assert(dst.buf != NULL);
  memcpy(dst.buf, str, sz);
  return dst;
}

static rc_ctrl_req_data_t gen_rc_ctrl(ue_id_e2sm_t const* ue)
{
  rc_ctrl_req_data_t c = {0};
  c.hdr.format = FORMAT_1_E2SM_RC_CTRL_HDR;
  c.hdr.frmt_1.ue_id = cp_ue_id_e2sm(ue);
  c.hdr.frmt_1.ric_style_type = 1;   /* Radio Bearer Control */
  c.hdr.frmt_1.ctrl_act_id = 2;      /* QoS flow mapping configuration */

  c.msg.format = FORMAT_1_E2SM_RC_CTRL_MSG;
  e2sm_rc_ctrl_msg_frmt_1_t* m = &c.msg.frmt_1;
  m->sz_ran_param = 2;
  m->ran_param = calloc(2, sizeof(seq_ran_param_t));
  assert(m->ran_param != NULL);
  m->ran_param[0].ran_param_id = 1;  /* DRB ID */
  m->ran_param[0].ran_param_val.type = ELEMENT_KEY_FLAG_TRUE_RAN_PARAMETER_VAL_TYPE;
  m->ran_param[0].ran_param_val.flag_true = calloc(1, sizeof(ran_parameter_value_t));
  m->ran_param[0].ran_param_val.flag_true->type = INTEGER_RAN_PARAMETER_VALUE;
  m->ran_param[0].ran_param_val.flag_true->int_ran = 5;

  m->ran_param[1].ran_param_id = 2;  /* list of QoS flows to modify */
  m->ran_param[1].ran_param_val.type = LIST_RAN_PARAMETER_VAL_TYPE;
  m->ran_param[1].ran_param_val.lst = calloc(1, sizeof(ran_param_list_t));
  ran_param_list_t* rpl = m->ran_param[1].ran_param_val.lst;
  rpl->sz_lst_ran_param = 1;
  rpl->lst_ran_param = calloc(1, sizeof(lst_ran_param_t));
  rpl->lst_ran_param[0].ran_param_struct.sz_ran_param_struct = 2;
  rpl->lst_ran_param[0].ran_param_struct.ran_param_struct = calloc(2, sizeof(seq_ran_param_t));
  seq_ran_param_t* rps = rpl->lst_ran_param[0].ran_param_struct.ran_param_struct;
  rps[0].ran_param_id = 4;           /* QoS flow identifier */
  rps[0].ran_param_val.type = ELEMENT_KEY_FLAG_TRUE_RAN_PARAMETER_VAL_TYPE;
  rps[0].ran_param_val.flag_true = calloc(1, sizeof(ran_parameter_value_t));
  rps[0].ran_param_val.flag_true->type = INTEGER_RAN_PARAMETER_VALUE;
  rps[0].ran_param_val.flag_true->int_ran = 10;
  rps[1].ran_param_id = 5;           /* QoS flow mapping indication */
  rps[1].ran_param_val.type = ELEMENT_KEY_FLAG_FALSE_RAN_PARAMETER_VAL_TYPE;
  rps[1].ran_param_val.flag_false = calloc(1, sizeof(ran_parameter_value_t));
  rps[1].ran_param_val.flag_false->type = INTEGER_RAN_PARAMETER_VALUE;
  rps[1].ran_param_val.flag_false->int_ran = 1;
  return c;
}

/* --------------------------------------------------------------- worker */

static void* worker(void* arg)
{
  (void)arg;
  float x[NF];
  for (;;) {
    pthread_mutex_lock(&q_mtx);
    while (q_len == 0 && !stopping)
      pthread_cond_wait(&q_cv, &q_mtx);
    if (q_len == 0 && stopping) {
      pthread_mutex_unlock(&q_mtx);
      break;
    }
    item_t it = q[q_head];
    q_head = (q_head + 1) % QCAP;
    size_t const qlen = q_len--;
    pthread_mutex_unlock(&q_mtx);

    int64_t const t0 = mono_ns();
    row_t r = {.seq = it.seq, .n_ue = it.n_ue, .qlen = qlen,
               .t_ind_us = it.recv_us,
               .t_q = (t0 - it.recv_ns) / 1e6, .t_act = -1.0};
    for (size_t u = 0; u < it.n_ue; ++u) {
      float const* w = windows + ((it.seq * 17 + u) % n_win) * REC * KPM;
      int64_t const a = mono_ns();
      aggregate(w, x);
      int64_t const b = mono_ns();
      volatile float s = infer(x);
      (void)s;
      int64_t const c = mono_ns();
      r.t_feat += (b - a) / 1e6;
      r.t_inf += (c - b) / 1e6;
      if (u == 0) { r.t_feat1 = (b - a) / 1e6; r.t_inf1 = (c - b) / 1e6; }
    }
    if (it.has_ue) {
      int64_t const a = mono_ns();
      rc_ctrl_req_data_t ctrl = gen_rc_ctrl(&it.ue);
      control_sm_xapp_api((global_e2_node_id_t*)node, 3, &ctrl);
      int64_t const b = mono_ns();
      free_rc_ctrl_req_data(&ctrl);
      free_ue_id_e2sm(&it.ue);
      r.t_act = (b - a) / 1e6;
    }
    if (n_rows < cap_rows)
      rows[n_rows++] = r;
  }
  return NULL;
}

/* ------------------------------------------------------- KPM subscription */

static const char* kpm_names[] = {
  "DRB.PdcpSduVolumeDL", "DRB.PdcpSduVolumeUL", "DRB.RlcSduDelayDl",
  "DRB.UEThpDl", "DRB.UEThpUl", "RRU.PrbTotDl", "RRU.PrbTotUl"};

static kpm_act_def_t gen_act_def(uint32_t period_ms)
{
  kpm_act_def_t dst = {0};
  dst.type = FORMAT_4_ACTION_DEFINITION;
  kpm_act_def_format_4_t* f4 = &dst.frm_4;
  f4->matching_cond_lst_len = 1;
  f4->matching_cond_lst = calloc(1, sizeof(matching_condition_format_4_lst_t));
  test_info_lst_t* ti = &f4->matching_cond_lst[0].test_info_lst;
  ti->test_cond_type = CQI_TEST_COND_TYPE;   /* all UEs, as in xapp_kpm_rc */
  ti->CQI = TRUE_TEST_COND_TYPE;
  ti->test_cond = calloc(1, sizeof(test_cond_e));
  *ti->test_cond = GREATERTHAN_TEST_COND;
  ti->test_cond_value = calloc(1, sizeof(test_cond_value_t));
  ti->test_cond_value->type = INTEGER_TEST_COND_VALUE;
  ti->test_cond_value->int_value = malloc(sizeof(int64_t));
  *ti->test_cond_value->int_value = 0;

  kpm_act_def_format_1_t* f1 = &f4->action_def_format_1;
  f1->gran_period_ms = period_ms;
  /* 16 measurement items per UE, the size of one record in the radio corpus;
     the emulated node implements seven names, so they are cycled. */
  f1->meas_info_lst_len = KPM;
  f1->meas_info_lst = calloc(KPM, sizeof(meas_info_format_1_lst_t));
  for (int i = 0; i < KPM; ++i) {
    meas_info_format_1_lst_t* mi = &f1->meas_info_lst[i];
    mi->meas_type.type = NAME_MEAS_TYPE;
    mi->meas_type.name = copy_str_to_ba(kpm_names[i % 7]);
    mi->label_info_lst_len = 1;
    mi->label_info_lst = calloc(1, sizeof(label_info_lst_t));
    mi->label_info_lst[0].noLabel = calloc(1, sizeof(enum_value_e));
    *mi->label_info_lst[0].noLabel = TRUE_ENUM_VALUE;
  }
  return dst;
}

static long env_long(const char* k, long d)
{
  const char* v = getenv(k);
  return v != NULL ? atol(v) : d;
}

static const char* env_str(const char* k)
{
  const char* v = getenv(k);
  if (v == NULL) { fprintf(stderr, "missing %s\n", k); exit(2); }
  return v;
}

int main(int argc, char* argv[])
{
  long const period = env_long("IDS_PERIOD_MS", 10);
  long const n_keep = env_long("IDS_N", 5000);
  long const warm = env_long("IDS_WARMUP", 200);
  const char* out = env_str("IDS_OUT");

  size_t bytes = 0;
  windows = read_all(env_str("IDS_WINDOWS"), &bytes);
  n_win = bytes / (sizeof(float) * REC * KPM);
  ort_init(env_str("IDS_MODEL"));
  double const worst = verify(env_str("IDS_REF"));
  printf("[IDS] verified %zu windows, max |C - Python| = %.3g\n", n_win, worst);
  if (worst > 1e-5) { fprintf(stderr, "C scores disagree with Python\n"); return 3; }

  cap_rows = (size_t)(n_keep + warm + 16);
  rows = calloc(cap_rows, sizeof(row_t));
  assert(rows != NULL);

  fr_args_t args = init_fr_args(argc, argv);
  init_xapp_api(&args);
  sleep(1);
  e2_node_arr_t nodes = e2_nodes_xapp_api();
  if (nodes.len == 0) { fprintf(stderr, "no E2 node connected\n"); return 4; }
  node = &nodes.n[0].id;

  pthread_t th;
  pthread_create(&th, NULL, worker, NULL);

  kpm_sub_data_t sub = {0};
  sub.ev_trg_def.type = FORMAT_1_RIC_EVENT_TRIGGER;
  sub.ev_trg_def.kpm_ric_event_trigger_format_1.report_period_ms = period;
  sub.sz_ad = 1;
  sub.ad = calloc(1, sizeof(kpm_act_def_t));
  *sub.ad = gen_act_def((uint32_t)period);
  sm_ans_xapp_t h = report_sm_xapp_api(&nodes.n[0].id, 2, &sub, sm_cb_kpm);
  if (!h.success) { fprintf(stderr, "KPM subscription failed\n"); return 4; }
  free_kpm_sub_data(&sub);

  int64_t const t_start = mono_ns();
  size_t const target = (size_t)(n_keep + warm);
  for (;;) {
    usleep(50000);
    pthread_mutex_lock(&q_mtx);
    size_t const done = n_rows;
    pthread_mutex_unlock(&q_mtx);
    if (done >= target) break;
    if ((mono_ns() - t_start) / 1e9 > 30.0 + 3.0 * target * period / 1000.0) {
      fprintf(stderr, "[IDS] timeout after %zu indications\n", done);
      break;
    }
  }
  double const wall = (mono_ns() - t_start) / 1e9;
  rm_report_sm_xapp_api(h.u.handle);

  pthread_mutex_lock(&q_mtx);
  stopping = true;
  pthread_cond_signal(&q_cv);
  pthread_mutex_unlock(&q_mtx);
  pthread_join(th, NULL);

  FILE* f = fopen(out, "w");
  assert(f != NULL);
  fprintf(f, "# period_ms=%ld warmup=%ld seen=%lu dropped=%lu wall_s=%.3f verify_max_abs=%.3g\n",
          period, warm, (unsigned long)n_seen, (unsigned long)n_dropped, wall, worst);
  fprintf(f, "seq,n_ue,qlen,t_ind_ms,t_q_ms,t_feat1_ms,t_inf1_ms,t_feat_ms,t_inf_ms,t_act_ms\n");
  for (size_t i = 0; i < n_rows; ++i) {
    row_t const* r = &rows[i];
    fprintf(f, "%lu,%zu,%zu,%.3f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
            (unsigned long)r->seq, r->n_ue, r->qlen, r->t_ind_us / 1000.0, r->t_q,
            r->t_feat1, r->t_inf1, r->t_feat, r->t_inf, r->t_act);
  }
  fclose(f);
  printf("[IDS] wrote %zu rows, seen %lu, dropped %lu, %.1f s\n", n_rows,
         (unsigned long)n_seen, (unsigned long)n_dropped, wall);

  while (try_stop_xapp_api() == false)
    usleep(1000);
  free_e2_node_arr(&nodes);
  free(rows);
  free(windows);
  return 0;
}
