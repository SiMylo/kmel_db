# kmel_db

A parser and generator for Kenwood Music Editor Light databases that works under Linux. The database is used by Kenwood car audio systems to allow searching by album, title, genre and artist. It also allows creation of playlists.

My Kenwood stereo only supports mp3 and wma media formats, so this is currently the default for this application.

## Requirements

You'll need Python version 3 or above.

In order to parse the media files you'll also need the [hsaudiotag3k](https://pypi.python.org/pypi/hsaudiotag3k) python package installed to run. The stock library will work if you don't have any multi-disc albums, and DapGen will fall back to renumbering discs if you do. I have a fork of hsaudiotag which reads disc numbers, which I hope to merge into the PyPi version soon.

In order to get defaults for the path argument, you'll also need [psutil](https://pypi.python.org/pypi/psutil).

## Database format
The db_format.md document attempts to explain the format of the database. It might be slightly behind the code.

## Generator
To generate a database, just type:

```bash
    ./DapGen.py /path/to/your/usb/drive
```

If you don't specify the path, the generator will process all mounted partitions of type FAT.

Use the '-h' option to see other options.

Current limitations:

* processes mp3 and wma only at this stage
* include and exclude regular expression parsing for media types not currently implemented
* processes pls playlists only at this stage
* international characters are sorted out of order, so "Bäpa" comes after "By The Hand Of My Father" rather than after "Banks of Newfoundland"

### renames.json
If you include a renames.json file, the tags for titles can be adjusted
for the Kenwood database.  This is useful if you want to store the full
titles in your library but your device is unable to display the entire
tag length.  Be aware that this can significantly increase runtime.

The file consists of a list of "transforms" which allows you to capture
parts of the original title (or the special tag ${Performer}) and use them
for the final title; and "substitutions" which allows you to take a regex
and replace it with a static value.  Note that because of the JSON spec, you'll have to escape your `\`.

Each of these items is performed in the order specified. 

For an example, suppose you had some symphonies in your library, and the
full name of the track looked something like this:
`Symphony No. 9 -iv. Presto; Allegro assai, Choral Finale on Schiller's 'Ode To Joy'`
which exceeds tag length limitations for the device.  You could shorten it
to something like
`Sy#9-4(LvB) Presto; Allegro assai (Ode To Joy)`
The renames.json file would include at least the following
```json
{
    "transforms": [
        ["Symphony No\\. ?(\\d+)[, -]*([iv]+\\.) (.*)", "Sy#$1-$2(${Performer})$3"],
    ],
    "substitutions": [
		[", Choral Finale on Schiller's 'Ode To Joy'", "(Ode To Joy)"],
		["Ludwig van Beethoven", "LvB"],
		["-iv\\.", "-4"],
    ]
}
```
and would do the following steps:
`Symphony No. 9 -iv. Presto; Allegro assai, Choral Finale on Schiller's 'Ode To Joy'`
-> `Sy#9-iv.(Ludwig van Beethoven) Presto; Allegro assai, Choral Finale on Schiller's 'Ode To Joy'`
-> `Sy#9-iv.(Ludwig van Beethoven) Presto; Allegro assai (Ode To Joy)`
-> `Sy#9-iv.(LvB) Presto; Allegro assai (Ode To Joy)`
-> `Sy#9-4(LvB) Presto; Allegro assai (Ode To Joy)`

Of course you could do this all in one substitution if you wanted to avoid
regex altogether.

## Parser
To parse a database, just type:

```bash
    ./KenwoodDBReader.py -i /path/to/kenwood.dap/file
```

It will print copious logs, used by me to analyse the database. I may ask for this output if you want me to look into a problem.

## Tests
To run the tests, just type:

```bash
    python3 -m kdbtest
```

If you have coverage installed, a test_coverage directory will be created with an HTML coverage report.

