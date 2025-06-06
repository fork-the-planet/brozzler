Brozzler Job Configuration
**************************

Jobs are used to brozzle multiple seeds and/or apply settings and scope rules,
as defined byusing YAML files. At least one seed URL must be specified.
All other configurartions are optional.

.. contents::

Example
=======

::

    id: myjob
    time_limit: 60 # seconds
    proxy: 127.0.0.1:8000 # point at warcprox for archiving
    ignore_robots: false
    max_claimed_sites: 2
    warcprox_meta:
      warc-prefix: job1
      stats:
        buckets:
        - job1-stats
    metadata: {}
    seeds:
    - url: http://one.example.org/
      warcprox_meta:
        warc-prefix: job1-seed1
        stats:
          buckets:
          - job1-seed1-stats
    - url: http://two.example.org/
      time_limit: 30
    - url: http://three.example.org/
      time_limit: 10
      ignore_robots: true
      scope:
        surt: http://(org,example,

How inheritance works
=====================

Most of the settings that apply to seeds can also be specified at the top
level, in which case all seeds inherit those settings. If an option is
specified both at the top level and at the seed level, the results are merged.
In cases of coflict, the seed-level value takes precedence.

In the example yaml above, ``warcprox_meta`` is specified at the top level and
at the seed level for the seed http://one.example.org/. At the top level we
have::

  warcprox_meta:
    warc-prefix: job1
    stats:
      buckets:
      - job1-stats

At the seed level we have::

    warcprox_meta:
      warc-prefix: job1-seed1
      stats:
        buckets:
        - job1-seed1-stats

The merged configuration as applied to the seed http://one.example.org/ will
be::

    warcprox_meta:
      warc-prefix: job1-seed1
      stats:
        buckets:
        - job1-stats
        - job1-seed1-stats

In this example:

- There is a collision on ``warc-prefix`` and the seed-level value wins.
- Since ``buckets`` is a list, the merged result includes all the values from
  both the top level and the seed level.

Settings
========

Top-level settings
------------------

``id``
~~~~~~
+--------+----------+--------------------------+
| type   | required | default                  |
+========+==========+==========================+
| string | no       | *generated by rethinkdb* |
+--------+----------+--------------------------+
An arbitrary identifier for this job. Must be unique across this deployment of
brozzler.

``max_claimed_sites``
~~~~~~~~~~~~~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| number | no       | *none*  |
+--------+----------+---------+
Puts a cap on the number of sites belonging to a given job that can be brozzled
simultaneously across the cluster. Addresses the problem of a job with many
seeds starving out other jobs.

``pdfs_only``
~~~~~~~~~~~~~~~~~~~~~
+---------+----------+-----------+
| type    | required | default   |
+=========+==========+===========+
| boolean | no       | ``false`` |
+---------+----------+-----------+
Limits capture to PDFs based on the MIME type set in the HTTP response's
Content-Type header. This value only impacts processing of outlinks within
Brozzler.

*Note: Ensuring comprehensive limiting to only PDFs requires an additional
entry in the Warcprox-Meta header `mime-type-filters` key.*

``seeds``
~~~~~~~~~
+------------------------+----------+---------+
| type                   | required | default |
+========================+==========+=========+
| list (of dictionaries) | yes      | *n/a*   |
+------------------------+----------+---------+
List of seeds. Each item in the list is a dictionary (associative array) which
defines the seed. It must specify ``url`` (see below) and can additionally
specify any seed settings.

Seed-level-only settings
------------------------
These settings can be specified only at the seed level, unlike the settings
below that can also be specified at the top level.

``url``
~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | yes      | *n/a*   |
+--------+----------+---------+
The seed URL. Brozzling starts here.

``username``
~~~~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
If set, used to populate automatically detected login forms. See explanation at
"password" below.

``password``
~~~~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
If set, used to populate automatically detected login forms. If ``username``
and ``password`` are configured for a seed, brozzler will look for a login form
on each page it crawls for that seed. A form that has a single text or email
field (the username), a single password field (``<input type="password">``),
and has ``method="POST"`` is considered to be a login form. When forms have
other fields like checkboxes and/or hidden fields, brozzler will leave
the default values in place. Brozzler submits login forms after page load.
Then brozzling proceeds as usual.

``video_capture``
~~~~~~~~~~~~~~~~~
+--------+----------+--------------------------+
| type   | required | default                  |
+========+==========+==========================+
| string | yes      | ``ENABLE_VIDEO_CAPTURE`` |
+--------+----------+--------------------------+
Determines the level of video capture for the seed. This is an enumeration with four possible values:

* ENABLE_VIDEO_CAPTURE (default): All video is captured.
* DISABLE_VIDEO_CAPTURE: No video is captured. This is effectively a
  combination of the next two values.
* BLOCK_VIDEO_MIME_TYPES: Any response with a Content-Type header containing
  the word "video" is not captured.
* DISABLE_YTDLP_CAPTURE: Video capture via yt-dlp is disabled.

*Note: Ensuring full video MIME type blocking requires an additional entry in
the Warcprox-Meta header `mime-type-filters` key.*

Seed-level / top-level settings
-------------------------------
These are seed settings that can also be specified at the top level, in which
case they are inherited by all seeds.

``metadata``
~~~~~~~~~~~~
+------------+----------+---------+
| type       | required | default |
+============+==========+=========+
| dictionary | no       | *none*  |
+------------+----------+---------+
Information about the crawl job or site. Could be useful for external
descriptive or informative metadata, but not used by brozzler in the course of
archiving.

``time_limit``
~~~~~~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| number | no       | *none*  |
+--------+----------+---------+
Time limit in seconds. If not specified, there is no time limit. Time limit is
enforced at the seed level. If a time limit is specified at the top level, it
is inherited by each seed as described above, and enforced individually on each
seed.

``proxy``
~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
HTTP proxy, with the format ``host:port``. Typically configured to point to
warcprox for archival crawling.

``ignore_robots``
~~~~~~~~~~~~~~~~~
+---------+----------+-----------+
| type    | required | default   |
+=========+==========+===========+
| boolean | no       | ``false`` |
+---------+----------+-----------+
If set to ``true``, brozzler will fetch pages that would otherwise be blocked
by `robots.txt rules
<https://en.wikipedia.org/wiki/Robots_exclusion_standard>`_.

``user_agent``
~~~~~~~~~~~~~~
+---------+----------+---------+
| type    | required | default |
+=========+==========+=========+
| string  | no       | *none*  |
+---------+----------+---------+
The ``User-Agent`` header brozzler will send to identify itself to web servers.
It is good ettiquette to include a project URL with a notice to webmasters that
explains why you are crawling, how to block the crawler via robots.txt, and how
to contact the operator if the crawl is causing problems.

``warcprox_meta``
~~~~~~~~~~~~~~~~~
+------------+----------+-----------+
| type       | required | default   |
+============+==========+===========+
| dictionary | no       | ``false`` |
+------------+----------+-----------+
Specifies the ``Warcprox-Meta`` header to send with every request, if ``proxy``
is configured. The value of the ``Warcprox-Meta`` header is a json blob. It is
used to pass settings and information to warcprox. Warcprox does not forward
the header on to the remote site. For further explanation of this field and
its uses see
https://github.com/internetarchive/warcprox/blob/master/api.rst

Brozzler takes the configured value of ``warcprox_meta``, converts it to
json and populates the Warcprox-Meta header with that value. For example::

    warcprox_meta:
      warc-prefix: job1-seed1
      stats:
        buckets:
        - job1-stats
        - job1-seed1-stats

becomes::

    Warcprox-Meta: {"warc-prefix":"job1-seed1","stats":{"buckets":["job1-stats","job1-seed1-stats"]}}

``scope``
~~~~~~~~~
+------------+----------+-----------+
| type       | required | default   |
+============+==========+===========+
| dictionary | no       | ``false`` |
+------------+----------+-----------+
Scope specificaion for the seed. See the "Scoping" section which follows.

Scoping
=======

The scope of a seed determines which links are scheduled for crawling ("in
scope") and which are not. For example::

    scope:
      accepts:
      - ssurt: com,example,//https:/
      - parent_url_regex: ^https?://(www\.)?youtube.com/(user|channel)/.*$
        regex: ^https?://(www\.)?youtube.com/watch\?.*$
      - surt: http://(com,google,video,
      - surt: http://(com,googlevideo,
      blocks:
      - domain: youngscholars.unimelb.edu.au
        substring: wp-login.php?action=logout
      - domain: malware.us
      max_hops: 20
      max_hops_off: 0

Toward the end of the process of brozzling a page, brozzler obtains a list of
navigational links (``<a href="...">`` and similar) on the page, and evaluates
each link to determine whether it is in scope or out of scope for the crawl.
Then, newly discovered links that are in scope are scheduled to be crawled, and
previously discovered links get a priority bump.

How brozzler applies scope rules
--------------------------------

Each scope rule has one or more conditions. If all of the conditions match,
then the scope rule as a whole matches. For example::

    - domain: youngscholars.unimelb.edu.au
      substring: wp-login.php?action=logout

This rule applies if the domain of the URL is "youngscholars.unimelb.edu.au" or
a subdomain, and the string "wp-login.php?action=logout" is found somewhere in
the URL.

Brozzler applies these logical steps to decide whether a URL is in or out of
scope:

1. If the number of hops from seed is greater than ``max_hops``, the URL is
   **out of scope**.
2. Otherwise, if any ``block`` rule matches, the URL is **out of scope**.
3. Otherwise, if any ``accept`` rule matches, the URL is **in scope**.
4. Otherwise, if the URL is at most ``max_hops_off`` hops from the last page
   that was in scope because of an ``accept`` rule, the url is **in scope**.
5. Otherwise (no rules match), the url is **out of scope**.

In cases of conflict, ``block`` rules take precedence over ``accept`` rules.

Scope rules may be conceived as a boolean expression. For example::

    blocks:
    - domain: youngscholars.unimelb.edu.au
      substring: wp-login.php?action=logout
    - domain: malware.us

means block the URL IF::

    ("domain: youngscholars.unimelb.edu.au" AND "substring: wp-login.php?action=logout") OR "domain: malware.us"

Automatic scoping based on seed URLs
------------------------------------
Brozzler usually generates an ``accept`` scope rule based on the seed URL. It
does this to fulfill the usual expectation that everything "under" the seed
will be crawled.

To generate the rule, brozzler canonicalizes the seed URL using the `urlcanon
<https://github.com/iipc/urlcanon>`_ library's "semantic" canonicalizer, then
removes the query string if any, and finally serializes the result in SSURT
[1]_ form. For example, a seed URL of
``https://www.EXAMPLE.com:443/foo//bar?a=b&c=d#fdiap`` becomes
``com,example,www,//https:/foo/bar``.

Brozzler derives its general approach to the seed surt from `heritrix
<https://github.com/internetarchive/heritrix3>`_, but differs in a few respects.

1. Unlike heritrix, brozzler does not strip the path segment after the last
   slash.
2. Canonicalization does not attempt to match heritrix exactly, though it
   usually does match.
3. Brozzler does no scheme munging. (When generating a SURT for an HTTPS URL,
   heritrix changes the scheme to HTTP. For example, the heritrix SURT for
   ``https://www.example.com/`` is ``http://(com,example,www,)`` and this means
   that all of ``http://www.example.com/*`` and ``https://www.example.com/*``
   are in scope. It also means that a manually specified SURT with scheme
   "https" does not match anything.)
4. Brozzler identifies seed "redirects" by retrieving the URL from the
   browser's location bar at the end of brozzling the seed page, whereas
   heritrix follows HTTP 3XX redirects. If the URL in the browser
   location bar at the end of brozzling the seed page differs from the seed
   URL, brozzler automatically adds a second ``accept`` rule to ensure the
   site is in scope, as if the new URL were the original seed URL. For example,
   if ``http://example.com/`` redirects to ``http://www.example.com/``, the
   rest of the ``www.example.com`` is in scope.
5. Brozzler uses SSURT instead of SURT.
6. There is currently no brozzler option to disable the automatically generated
   ``accept`` rules.

Scope settings
--------------

``accepts``
~~~~~~~~~~~
+------+----------+---------+
| type | required | default |
+======+==========+=========+
| list | no       | *none*  |
+------+----------+---------+
List of scope rules. If any of the rules match, the URL is within
``max_hops`` from seed, and none of the ``block`` rules apply, then the URL is
in scope and brozzled.

``blocks``
~~~~~~~~~~~
+------+----------+---------+
| type | required | default |
+======+==========+=========+
| list | no       | *none*  |
+------+----------+---------+
List of scope rules. If any of the rules match, then the URL is deemed out
of scope and NOT brozzled.

``max_hops``
~~~~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| number | no       | *none*  |
+--------+----------+---------+
Maximum number of hops from seed.

``max_hops_off``
~~~~~~~~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| number | no       | 0       |
+--------+----------+---------+
Expands the scope to include URLs up to this many hops from the last page that
was in scope because of an ``accept`` rule.

Scope rule conditions
---------------------

``domain``
~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
Matches if the host part of the canonicalized URL is ``domain`` or a
subdomain.

``substring``
~~~~~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
Matches if ``substring`` value is found anywhere in the canonicalized URL.

``regex``
~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
Matches if the full canonicalized URL matches a regular expression.

``ssurt``
~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
Matches if the canonicalized URL in SSURT [1]_ form starts with the ``ssurt``
value.

``surt``
~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
Matches if the canonicalized URL in SURT [2]_ form starts with the ``surt``
value.

``parent_url_regex``
~~~~~~~~~~~~~~~~~~~~
+--------+----------+---------+
| type   | required | default |
+========+==========+=========+
| string | no       | *none*  |
+--------+----------+---------+
Matches if the full canonicalized parent URL matches a regular expression.
The parent URL is the URL of the page in which a link is found.

Using ``warcprox_meta``
=======================
``warcprox_meta`` plays a very important role in brozzler job configuration.
It sets the filenames of the WARC files created by a job. For example, if each
seed should have a different WARC filename prefix, you might configure a job
this way::

    seeds:
    - url: https://example.com/
      warcprox_meta:
        warc-prefix: seed1
    - url: https://archive.org/
      warcprox_meta:
        warc-prefix: seed2

``warcprox_meta`` may also be used to limit the size of the job. For example,
this configuration will stop the crawl after about 100 MB of novel content has
been archived::

    seeds:
    - url: https://example.com/
    - url: https://archive.org/
    warcprox_meta:
      stats:
        buckets:
        - my-job
      limits:
        my-job/new/wire_bytes: 100000000

To prevent any URLs from a host from being captured, it is not sufficient to use
a ``scope`` rule as described above. That kind of scoping only applies to
navigational links discovered in crawled pages. To make absolutely sure that no
url from a given host is fetched--not even an image embedded in a page--use
``warcprox_meta`` like so::

    warcprox_meta:
      blocks:
      - domain: spammy.com

For complete documentation on the ``warcprox-meta`` request header, see
https://github.com/internetarchive/warcprox/blob/master/api.rst#warcprox-meta-http-request-header

.. [1] SSURT is described at https://github.com/iipc/urlcanon/blob/master/ssurt.rst
.. [2] SURT is described at http://crawler.archive.org/articles/user_manual/glossary.html
