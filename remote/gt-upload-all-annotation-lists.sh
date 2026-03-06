#!/usr/bin/env bash

BATCHSIZE=10
BAR_CHAR='#'
EMPTY_CHAR=' '
start_time=$(date +%s)

fatal() {
  echo '[FATAL]' "$@" >&2
  exit 1
}

progress-bar() {
  local current=$1
  local len=$2

  local perc_done=$((current * 100 / len))

  local current_time=$(date +%s)
  local elapsed_time=$((current_time - start_time))
  local estimated_time=$((elapsed_time * len / current - elapsed_time))

  local run=$(seconds-to-dhms $elapsed_time)
  local dhms=$(seconds-to-dhms $estimated_time)

  local suffix=" $current/$len ($perc_done%) | RUN: ${run} | ETR: ${dhms}"

  local length=$((COLUMNS - ${#suffix} - 2))
  local num_bars=$((perc_done * length / 100))

  local i
  local s='['
  for ((i = 0; i < num_bars; i++)); do
    s+=$BAR_CHAR
  done
  for ((i = num_bars; i < length; i++)); do
    s+=$EMPTY_CHAR
  done
  s+=']'
  s+=$suffix

  printf '\e7' # save the cursor location
  printf '\e[%d;%dH' "$LINES" 0 # move cursor to the bottom line
  printf '\e[0K' # clear the line
  printf '\033[34m' # Set color to blue
  printf '%s' "$s" # print the progress bar
  printf '\033[0m' # Reset color
  printf '\e8' # restore the cursor location
}

seconds-to-dhms() {
  local total=$1
  local days hours minutes seconds

  (( days    = total / 86400 ))
  (( hours   = (total % 86400) / 3600 ))
  (( minutes = (total % 3600) / 60 ))
  (( seconds = total % 60 ))

  printf "%d:%02d:%02d:%02d\n" "$days" "$hours" "$minutes" "$seconds"
}

process-inventory() {
  local invnrs=("$@")
  make --jobs 3 --keep-going $(for i in "${invnrs[@]}"; do printf "upload-$i "; done)
  for invnr in "${invnrs[@]}"; do
    echo $invnr >> work/inv-done.lst
  done
}

init-term() {
  printf '\n' # ensure we have space for the scrollbar
  printf '\e7' # save the cursor location
  printf '\e[%d;%dr' 0 "$((LINES - 1))" # set the scrollable region (margin)
  printf '\e8' # restore the cursor location
  printf '\e[1A' # move cursor up
}

deinit-term() {
  printf '\e7' # save the cursor location
  printf '\e[%d;%dr' 0 "$LINES" # reset the scrollable region (margin)
  printf '\e[%d;%dH' "$LINES" 0 # move cursor to the bottom line
  printf '\e[0K' # clear the line
  printf '\e8' # reset the cursor location
}

send-notification() {
  curl -H "Tags: globalise" -d "$@" https://ntfy.sh/bb-work > /dev/null
}

main() {
  shopt -s globstar nullglob checkwinsize
  # this line is to ensure LINES and COLUMNS are set
  (:)

  trap deinit-term exit
  trap init-term winch
  init-term

  readarray -t invnrs < work/inv-todo.lst
  local len=${#invnrs[@]}
  echo "uploading $len inventories"

  local i
  for ((i = 0; i < len; i += BATCHSIZE)); do
    progress-bar "$((i+1))" "$len"
    process-inventory "${invnrs[@]:i:BATCHSIZE}"
  done
  progress-bar "$len" "$len"
  local current_time=$(date +%s)
  local elapsed_time=$((current_time - start_time))
  local run=$(seconds-to-dhms $elapsed_time)
  echo "done in $run"
  send-notification "gt-upload-all-annotation-lists finished in $run"
}

main "$@"
