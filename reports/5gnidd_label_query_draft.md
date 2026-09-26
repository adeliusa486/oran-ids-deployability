Draft email to the 5G-NIDD authors (not sent)

To: Sehan Samarakoon <sehan.samarakoon@oulu.fi>
Cc: Yushan Siriwardhana <yushan.siriwardhana@oulu.fi>, Madhusanka Liyanage <madhusanka@ucd.ie>
(addresses as listed in the dataset's README.pdf)
Subject: 5G-NIDD: UDP-flood flows labeled Benign in the BS1 capture

Dear Dr. Samarakoon,

We use 5G-NIDD (Fairdata dataset 9d13ef28-2ca7-44b0-9950-225359afac65) as a target corpus in a study of cross-corpus intrusion detection for O-RAN. While checking the labels we found flows that appear to be mislabeled, and we would like to confirm our reading before our paper goes to press.

In Combined.csv, 281,525 flows labeled Benign are identical in every field except the row index, Seq and Offset to flows labeled UDPFlood. BTS1_BTS2_fields_preserved.csv, which aligns with Combined.csv row for row, shows where they come from:

1. All 281,525 are in BS1_each_attack_csv/UDPFlood1.csv, and all are UDP flows from 10.155.15.7 to 10.41.150.68 between minute 03:49.0 and 13:32.4.
2. In BS2's UDP-flood capture, exactly this host pair, protocol and time window forms the 281,529 flows labeled UDPFlood.
3. The attack labeled in UDPFlood1.csv comes from 10.155.15.4 and targets the same address.

Our reading is that the BS1 capture also recorded the flood launched from the BS2 side, and that only the BS1 attacker was labeled in that file. These flows make up 59% of the Benign class. Could you confirm whether they should be labeled UDPFlood, and whether a corrected release is planned?

Until we hear from you, we report every result both with and without these flows and change no label. We are glad to send our scripts and the list of affected rows.

Kind regards,
[name, affiliation]
