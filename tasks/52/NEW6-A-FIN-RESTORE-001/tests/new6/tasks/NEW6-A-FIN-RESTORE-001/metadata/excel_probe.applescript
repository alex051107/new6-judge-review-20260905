on run argv
 tell application "Microsoft Excel"
  set targetBook to open workbook workbook file name (item 1 of argv) update links do not update links read only false ignore read only recommended true
  repeat with targetSheet in worksheets of targetBook
   calculate targetSheet
  end repeat
  save targetBook
  close targetBook saving no
 end tell
end run
