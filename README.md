boilerpot
=========

Templating content from HTML.  A Python do-alike to boilerpipe.

boilerpipe (http://code.google.com/p/boilerpipe/) is a Java program that looks at HTML tags and tries to deduce where the actual content is sans navigation, headers & footers, etc.

This is a rough rewrite of that written in Python and should be considered super duper alpha.  I did it during a 2-day company (Curata.com) hackathon.  I have even run a comparison of its output against its step-father let alone done any corpus comparisons against commoncrawl.org.  Consider yourself warned.

The only advantages over boilerpipe is that it is easier to interface with Python and the code is much more accessible: 500 lines of Python in one module versus 9000 lines of Java scattered accross a bazillion files and directories (I hate me some directories).