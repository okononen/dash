dash
====

About this project
------------------

Dash is a project led by [Olga Baysal](https://cs.uwaterloo.ca/~obaysal/) from
the University of Waterloo to help provide Mozilla developers with customized
dashboards that summarize their current Bugzilla issues. The project was started
after investigating the <a href="https://wiki.mozilla.org/Bugzilla_Anthropology">Mozilla Anthropology</a>
interviews. The project is in active development; if you have any questions,
comments, or suggestions, please <a href="mailto:obaysal@uwaterloo.ca?Subject=Feedback%20on%20Developer%20Dash"
target="_top">get in touch</a>.

  * The most related article relevant to this project is [here](developer_dash_ieeesoft13.pdf)
  * Our analysis of the Mozilla Anthropology Interviews is <a href="http://www.cs.uwaterloo.ca/research/tr/2012/CS-2012-10.pdf">here</a>.
  * The original version of this dashboard, which relies on Bugzilla REST API,
can be found <a href="http://claw.cs.uwaterloo.ca/dash">here</a>.
  * This version was created by <a href="https://cs.uwaterloo.ca/~okononen">Oleksii Kononenko</a>

Installation
------------

The server side requires Apache, with Python CGI scripting enabled.  The server Python installation also requires:

  * pytz: ```pip install pytz```
  * HTML: Found at [http://www.decalage.info/files/HTML.py-0.04.zip](http://www.decalage.info/files/HTML.py-0.04.zip)
You may need to delete ```python\Lib\site-packages\html.py``` before you run
```setup.py```

