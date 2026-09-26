add_executable(xapp_ids_timing
  xapp_ids_timing.c
  ../../../../src/util/alg_ds/alg/defer.c
  )

target_include_directories(xapp_ids_timing PRIVATE ${ORT_DIR}/include)

target_link_libraries(xapp_ids_timing
                      PUBLIC
                      e42_xapp
                      ${ORT_DIR}/lib/libonnxruntime.so
                      -Wl,-rpath,${ORT_DIR}/lib
                      -pthread
                      -lsctp
                      -ldl
                      -lm
                      )
