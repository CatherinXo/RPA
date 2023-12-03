# RPA Challenge

The tasks for the challenge is mentioned in `RPA Challenge - Fresh news.pdf`

## Configfile

Configuration file with search_phrase, sections and months

Find the sample `configfile`

Script: `rpa.py`

## Output

Output excel sheets processed by this script is present in `output` dir. Excel sheets are named in `$search_phrase$section1$section2...$months` format

Images downloaded as well is found in `output/images` specific subdirs. Deleted some subdirs due to zip file size issue to be sent over email.

## Hardening

Below items can be worked further to upgrade the current codebase

- Add logs
- For various inputs, check errors
- Can implement csv chunk write
- Can implement processing in chunks


## NOTE
- Cant chose none news section
- Date range not working in prod UI itself, need to script out
