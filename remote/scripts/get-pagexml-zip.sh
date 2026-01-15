#!/usr/bin/env bash
PREFIX=$1
expect <<EOI
set timeout -1
spawn sftp -P 2222 hucdrive.huc.knaw.nl
expect "Password:"
send "$HUCDRIVEPW\r"
expect "sftp>"
send "cd globalise\r"
expect "sftp>"
send "mget $PREFIX-pagexml.zip data/pagexml/$PREFIX.zip\r"
expect "sftp>"
send "bye\r"
EOI
