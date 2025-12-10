This document is a list of python coding standards. To add a new standard copy the template below and modify it.

see also http://emg.nysbc.org/wiki/index.php/Appionscripts_formatting_rules

------------------------------------------------------------------------

## [Name of Coding Standard]{.underline}

### Definition

What is the coding standard

### Justification

Why is the coding standard important

### Example

GOOD:

    this is a good example code

BAD:

    this is a bad example code

------------------------------------------------------------------------

# Python Coding Standards for AMI

------------------------------------------------------------------------

## [Use tabs instead of spaces]{.underline}

### Definition

Use tabs instead of spaces for inline code

### Justification

It is important to be consistent. People like different sizes of columns, some like 8 spaces, others 4, 3, or 2. With tabs each individual can customize their viewer.

### Example

GOOD:

    if True:
    <tab>while True:
    <tab><tab>print "tab"
    <tab>break

BAD:

    if True:
       while True:
            print "tab"
       break

------------------------------------------------------------------------

## [Checking beginning or ending of strings]{.underline}

### Definition

Use ''.startswith() and ''.endswith() instead of string slicing to check for prefixes or suffixes.

### Justification

startswith() and endswith() are cleaner and less error prone.

### Example

GOOD:

    if foo.startswith('bar'): 

BAD:

    if foo[:3] == 'bar':

------------------------------------------------------------------------

## [Never use `from module import *`]{.underline}

### Definition

Never use `from module import *`, use `import module` instead

### Justification

It is hard to track where functions come from when `import *` is used

### Example

GOOD:

    import numpy
    a = numpy.ones((3,3))

BAD:

    from numpy import *
    a = ones((3,3))

------------------------------------------------------------------------

## [Appion image data naming conventions]{.underline}

### Definition

1.  never use 'image' or 'img'
2.  use 'imgdict' for image dictionaries
3.  use 'imgarray' for image numarrays
4.  use 'imgname' for image filenames
5.  use 'imgtree' for the main list of image dictionaries
6.  use 'imglist' for a list of image data

### Justification

If you are consistent with your names people can read your code.

### Example

GOOD:

    for imgdict in imgtree:
        imgarray = imgdict['image']
        imgname = imgdict['filename']

BAD:

    for image in imgs:
        array = image['image']
        name = image['filename']

------------------------------------------------------------------------

## [Use descriptive variables]{.underline}

### Definition

Use descriptive variables, `asdf` is not a variable.

### Justification

No one understands shorthand variables.

### Example

GOOD:

    imgarray = mrc.read('leginon_image.mrc')
    particle1 = imgarray[47, 21]
    particle1 = imgarray[10, 15]
    stack = [particle1, particle2]

BAD:

    i = mrc.read('x.mrc')
    prtl1 = i[47, 21]
    prtl2 = i[10, 15]
    s = [prtl1, prtl2]

------------------------------------------------------------------------

## [Location of functions]{.underline}

### Definition

Functions that have a global use, should go in appionlib folder.
Functions that will only be used by a single program go into that program's file.
Upload to the database function are typically only used by a single program and should be within that program not in appionlib

### Justification

Keep the code clean an organized.

### Example

GOOD:

    from appionlib import commonFunctions

    class AppionScript():
     def customUploadToDB(self):
       """stuff"""
     def run(self):
       commonFunctions.commonFunction()
       self.customUploadToDB()

BAD:

    from appionlib import apUploadCustom

    class AppionScript():
     def commonFunction(self):
        """stuff"""
     def run(self):
       self.commonFunction()
       apUploadCustom.customUploadToDB()
