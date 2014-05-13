#!/usr/bin/python
import calendar
from string import Template
from time import gmtime
from datetime import datetime
from datetime import timedelta
import time
import cgi
import codecs
import os

import requests
from pytz import timezone
import pytz
import HTML

from util.cnv import CNV
from QueryBuilder import QueryBuilder


def pretty_date(_time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.now(timezone('UTC'))

    if type(_time) is int or type(_time) is long:
        diff = now - datetime.utcfromtimestamp(_time).replace(tzinfo=pytz.utc)
    elif isinstance(_time, datetime):
        diff = now - _time
    elif not _time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if (day_diff == 7) or (day_diff < 14):
        return str(day_diff / 7) + " week ago"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago"


def main():
    cgi_line = """Content-type:text/html\r\n\r\n
    """

    form = cgi.FieldStorage()

    if form.getvalue('username'):
        username = form.getvalue('username')
    else:
        username = None

    if form.getvalue('length'):
        length = form.getvalue('length')
    else:
        length = None

    if None in (username, length):
        try:
            raise Exception('Required fields can not be empty')
        except Exception as e:
            print cgi_line + '<h3>An error occured: ' + str(e) + '. </h3>'
    else:
        try:
            filename = "settings.json"
            filename = "/".join(filename.split(os.sep))
            # global_start_time = time.clock()
            dd = datetime.utcnow()
            current_ts = ConvertToTimestamp(dd)
            end_ts = current_ts
            start_ts = ConvertToTimestamp(dd - timedelta(days=int(length)))

            with codecs.open(filename, "r", encoding="utf-8") as settings_file:
                json = settings_file.read()
            settings = CNV.JSON2object(json, flexible=True)
            es_bugs_url = settings.bugs.host + ":" + unicode(settings.bugs.port) + "/" + settings.bugs.index + "/" + settings.bugs.type
            es_comments_url = settings.comments.host + ":" + unicode(settings.comments.port) + "/" + settings.comments.index + "/" + settings.comments.type

            assigned, submitted, cc_comment, patchlog, reviews, bugids_with_missing_desc = GetDataFromES(username, start_ts, end_ts, current_ts, es_bugs_url, es_comments_url)
            # t = time.clock()
            history, assigned, submitted, cc_comment, patchlog, reviews = PreProcessData(assigned, submitted, cc_comment, patchlog, reviews, dict())
            content = BuildPage(history, assigned, submitted, cc_comment, patchlog, reviews)
            # print "\npreparing html:", time.clock() - t
            # print "\nglobal execution time", time.clock() - global_start_time
            print cgi_line + content
        except Exception as e:
            print cgi_line + '<h3>An error occured: ' + str(e) + '. </h3>'


def GetDataFromES(username, start_ts, end_ts, current_ts, es_bugs_url, es_comments_url):
    submitted_raw = []
    assigned_raw = []
    cc_raw = []
    commented_raw = []
    patchlog_raw = []
    reviews_pending_raw = []
    reviews_done_raw = []
    bugids_with_missing_desc = set()
    print_debug_info = False

    startTime = time.clock()
    response = Search(es_bugs_url, QueryBuilder.SubmittedBugs(username, start_ts, end_ts, current_ts))
    if print_debug_info: print "submitted total hits: ", response.hits.total
    if response.hits.total > 0:
        for hit in response.hits.hits:
            desc = "N/A"
            if hit.fields.short_desc:
                desc = hit.fields.short_desc
            else:
                bugids_with_missing_desc.add(hit.fields.bug_id)
            submitted_raw.append([hit.fields.bug_id, desc, hit.fields.modified_ts / 1000, ConvertToTooltipString(hit.fields.changes)])
    if print_debug_info: print "submitted:" + str((time.clock() - startTime))

    startTime = time.clock()
    response = Search(es_bugs_url, QueryBuilder.AssignedBugs(username, start_ts, end_ts, current_ts))
    if print_debug_info: print "assigned total hits: ", response.hits.total
    if response.hits.total > 0:
        for hit in response.hits.hits:
            desc = "N/A"
            if hit.fields.short_desc:
                desc = hit.fields.short_desc
            else:
                bugids_with_missing_desc.add(hit.fields.bug_id)
            assigned_raw.append([hit.fields.bug_id, desc, hit.fields.modified_ts / 1000, ConvertToTooltipString(hit.fields.changes)])
    if print_debug_info: print "assigned:" + str((time.clock() - startTime))

    startTime = time.clock()
    response = Search(es_bugs_url, QueryBuilder.CC(username, start_ts, end_ts, current_ts))
    if print_debug_info: print "CC total hits: ", response.hits.total
    if response.hits.total > 0:
        for hit in response.hits.hits:
            desc = "N/A"
            if hit.fields.short_desc:
                desc = hit.fields.short_desc
            else:
                bugids_with_missing_desc.add(hit.fields.bug_id)
            cc_raw.append([hit.fields.bug_id, desc, hit.fields.modified_ts / 1000, ConvertToTooltipString(hit.fields.changes)])
    if print_debug_info: print "cc:" + str((time.clock() - startTime))

    ### Comments (need to query two different indexes) ###
    startTime = time.clock()
    # First we need to come up with some value of timestamp to filter out the list of comments
    subTimer = time.clock()
    response = Search(es_bugs_url, QueryBuilder.MinCreatedTimestamp(start_ts, end_ts, current_ts))
    if response.hits.total > 0:
        filter_ts = response.hits.hits[0].fields.created_ts
    else:
        filter_ts = current_ts  # otherwise it would be '0' and would load all comments
    if print_debug_info: print "\ttime(min created_ts): " + str((time.clock() - subTimer))
    if print_debug_info: print "\tmin created_ts =", filter_ts / 1000, gmtime(filter_ts / 1000)

    subTimer = time.clock()
    # Now get ids of all those bugs where 'username' made a comment after 'filter_ts'
    response = Search(es_comments_url, QueryBuilder.BugsWithCommentsFromUser(username, filter_ts))
    bugs_comments = set()   # put all values into set to automatically remove all duplicates
    if response.hits.total > 0:
        for comment in response.hits.hits:
            bugs_comments.add(comment.fields.bug_id)
    if print_debug_info: print "\ttotal found comments: ", response.hits.total
    if print_debug_info: print "\ttime(list of bugs' ids): " + str((time.clock() - subTimer))

    # subTimer = time.clock()
    response = Search(es_bugs_url, QueryBuilder.BugsForThePeriod(start_ts, end_ts, current_ts, str(list(bugs_comments))))
    if response.hits.total > 0:
        for hit in response.hits.hits:
            desc = "N/A"
            if hit.fields.short_desc:
                desc = hit.fields.short_desc
            else:
                bugids_with_missing_desc.add(hit.fields.bug_id)
            commented_raw.append([hit.fields.bug_id, desc, hit.fields.modified_ts / 1000, ConvertToTooltipString(hit.fields.changes)])
    if print_debug_info: print "\ttotal found bugs: ", response.hits.total
    if print_debug_info: print "\ttime(final query): " + str((time.clock() - subTimer))
    ### ============================================ ###
    if print_debug_info: print "comments:" + str((time.clock() - startTime))

    startTime = time.clock()
    response = Search(es_bugs_url, QueryBuilder.PatchLog(username, start_ts, end_ts, current_ts))
    if print_debug_info: print "'Patch log' total hits: ", response.hits.total
    if response.hits.total > 0:
        for hit in response.hits.hits:
            bug = hit.fields
            if bug.attachments:
                for attachment in bug.attachments:
                    if attachment["attachments.ispatch"] and attachment.created_by == username:
                        if attachment.flags:
                            for flag in attachment.flags:
                                if flag.request_status in ['?', '+', '-']:
                                    patchlog_raw.append([attachment.attach_id, hit.fields.bug_id, flag.request_type + flag.request_status, flag.modified_by, hit.fields.modified_ts / 1000,
                                                         ConvertToTooltipString(hit.fields.changes)])
    if print_debug_info: print "patchlog:" + str((time.clock() - startTime))

    startTime = time.clock()
    response = Search(es_bugs_url, QueryBuilder.PendingReviews(username, current_ts))
    if print_debug_info: print "'Pending reviews' total hits: ", response.hits.total
    if response.hits.total > 0:
        for hit in response.hits.hits:
            bug = hit.fields
            if bug.attachments:
                for attachment in bug.attachments:
                    if attachment["attachments.ispatch"]:
                        if attachment.flags:
                            for flag in attachment.flags:
                                if flag.request_status == '?' and flag.requestee == username:
                                    reviews_pending_raw.append([attachment.attach_id, hit.fields.bug_id, flag.request_type + flag.request_status, flag.modified_by, hit.fields.modified_ts / 1000,
                                                                ConvertToTooltipString(hit.fields.changes)])
    if print_debug_info: print "pending reviews:" + str((time.clock() - startTime))

    startTime = time.clock()
    response = Search(es_bugs_url, QueryBuilder.FinishedReviews(username, start_ts, end_ts, current_ts))
    if print_debug_info: print "'Finished reviews' total hits: ", response.hits.total
    if response.hits.total > 0:
        for hit in response.hits.hits:
            bug = hit.fields
            if bug.attachments:
                for attachment in bug.attachments:
                    if attachment["attachments.ispatch"]:
                        if attachment.flags:
                            for flag in attachment.flags:
                                if flag.request_status in ['+', '-'] and flag.modified_by == username:
                                    reviews_done_raw.append([attachment.attach_id, hit.fields.bug_id, flag.request_type + flag.request_status, attachment.created_by, hit.fields.modified_ts / 1000,
                                                             ConvertToTooltipString(hit.fields.changes)])
    if print_debug_info: print "finished reviews:" + str((time.clock() - startTime))

    submitted = list(set(tuple(elt) for elt in submitted_raw))
    assigned = list(set(tuple(elt) for elt in assigned_raw))
    cc_comment = commented_raw + cc_raw
    cc_comment = list(set(tuple(elt) for elt in cc_comment))
    reviews = reviews_pending_raw + reviews_done_raw
    reviews = list(set(tuple(elt) for elt in reviews))
    patchlog = list(set(tuple(elt) for elt in patchlog_raw))

    return assigned, submitted, cc_comment, patchlog, reviews, bugids_with_missing_desc


def PreProcessData(assigned, submitted, cc_comment, patchlog, reviews, bug_x_desc):
    assigned_final = []
    submitted_final = []
    cc_comment_final = []
    patchlog_final = []
    reviews_final = []

    for elt in assigned:
        desc = elt[1]
        if bug_x_desc.has_key(elt[0]):
            desc = bug_x_desc.get(elt[0])
        assigned_final.append((HTML.link(elt[0], 'https://bugzilla.mozilla.org/show_bug.cgi?id=' + str(elt[0])),
                               cgi.escape(desc),
                               '<div><span class="lastTouch" title="' + str(elt[2]) + '">' + str(pretty_date(elt[2])) + '</span></div>',
                               cgi.escape(elt[3])))

    for elt in submitted:
        desc = elt[1]
        if bug_x_desc.has_key(elt[0]):
            desc = bug_x_desc.get(elt[0])
        submitted_final.append((HTML.link(elt[0], 'https://bugzilla.mozilla.org/show_bug.cgi?id=' + str(elt[0])),
                                cgi.escape(desc),
                                '<div><span class="lastTouch" title="' + str(elt[2]) + '">' + str(pretty_date(elt[2])) + '</span></div>',
                                cgi.escape(elt[3])))

    for elt in cc_comment:
        desc = elt[1]
        if bug_x_desc.has_key(elt[0]):
            desc = bug_x_desc.get(elt[0])
        cc_comment_final.append((HTML.link(elt[0], 'https://bugzilla.mozilla.org/show_bug.cgi?id=' + str(elt[0])),
                                 cgi.escape(desc),
                                 '<div><span class="lastTouch" title="' + str(elt[2]) + '">' + str(pretty_date(elt[2])) + '</span></div>',
                                 cgi.escape(elt[3])))

    history = list(set(submitted_final + assigned_final + cc_comment_final))

    for elt in patchlog:
        patchlog_final.append((HTML.link(elt[0], 'https://bug' + str(elt[1]) + '.bugzilla.mozilla.org/attachment.cgi?id=' + str(elt[0])),
                               HTML.link(elt[1], 'https://bugzilla.mozilla.org/show_bug.cgi?id=' + str(elt[1])),
                               elt[2],
                               elt[3],
                               '<div><span class="lastTouch" title="' + str(elt[4]) + '">' + str(pretty_date(elt[4])) + '</span></div>',
                               cgi.escape(elt[5])))

    for elt in reviews:
        reviews_final.append((HTML.link(elt[0], 'https://bug' + str(elt[1]) + '.bugzilla.mozilla.org/attachment.cgi?id=' + str(elt[0])),
                              HTML.link(elt[1], 'https://bugzilla.mozilla.org/show_bug.cgi?id=' + str(elt[1])),
                              elt[2],
                              elt[3],
                              '<div><span class="lastTouch" title="' + str(elt[4]) + '">' + str(pretty_date(elt[4])) + '</span></div>',
                              cgi.escape(elt[5])))

    return history, assigned_final, submitted_final, cc_comment_final, patchlog_final, reviews_final


def BuildPage(history, assigned, submitted, cc_comment, patchlog, reviews):
    # Main Content
    main = """
    <div id="column">
    <div id="box-1" class="flexboxHFill">
    <script src="http://claw.cs.uwaterloo.ca/~okononen/js/tracking.js" type="text/javascript"></script>
    """

    # Left panel (history, assigned, submitted, cc, commented)
    tab_issues = """
    <h1> Issues</h1><div id="cell">
    <div class="tabs">
    """

    tab_assigned = """
    <div class="tab">
    <input type="radio" onclick="_gaq.push(["_trackEvent", "Tab", "Selected", this]);" href="#tab1" id="tab-1" name="tab-group-1">
    <label for="tab-1">Assigned</label>
    <div class="content">
    """
    assigned_html = HTML.Table(header_row=['BugID', 'Summary', 'Last Touched'])
    for row in sorted(assigned, key=lambda x: x[2], reverse=True):
        title = {}
        if row[3]:
            title["title"] = row[3]
        r = HTML.TableRow(row[:3], attribs=title)
        assigned_html.rows.append(r)
    content_assigned = str(assigned_html)
    close_assigned = "</div></div>"             # content, tab-1

    tab_reported = """
    <div class="tab">
    <input type="radio" href="#tab2" id="tab-2" name="tab-group-1">
    <label for="tab-2">Reported</label>
    <div class="content">
    """
    submitted_html = HTML.Table(header_row=['BugID', 'Summary', 'Last Touched'])
    for row in sorted(submitted, key=lambda x: x[2], reverse=True):
        title = {}
        if row[3]:
            title["title"] = row[3]
        r = HTML.TableRow(row[:3], attribs=title)
        submitted_html.rows.append(r)
    content_reported = str(submitted_html)
    close_reported = "</div></div>"             # content, tab-2

    tab_cc = """
    <div class="tab">
    <input type="radio" href="#tab3" id="tab-3" name="tab-group-1">
    <label for="tab-3">CC, Comments</label>
    <div class="content">
    """
    cc_comment_html = HTML.Table(header_row=['BugID', 'Summary', 'Last Touched'])
    for row in sorted(cc_comment, key=lambda x: x[2], reverse=True):
        title = {}
        if row[3]:
            title["title"] = row[3]
        r = HTML.TableRow(row[:3], attribs=title)
        cc_comment_html.rows.append(r)
    content_cc = str(cc_comment_html)
    close_cc = "</div></div>"                   # content, tab-3

    tab_activity = """
    <div class="tab">
    <input type="radio" href="#tab4" id="tab-4" name="tab-group-1" checked>
    <label for="tab-4">Activity</label>
    <div class="content">
    """
    history_html = HTML.Table(header_row=['BugID', 'Summary', 'Last Touched'])
    for row in sorted(history, key=lambda x: x[2], reverse=True):
        title = {}
        if row[3]:
            title["title"] = row[3]
        r = HTML.TableRow(row[:3], attribs=title)
        history_html.rows.append(r)
    content_activity = str(history_html)
    close_activity = "</div></div>"             # content, tab-4

    close_issues = "</div></div></div></div>"   # tabs, cell, box-1, column

    # Right panel (Patches and Reviews View)
    tab_patches = """
    <div id="column"><div id="box-2" class="flexboxHFill">
    <h1> Patches and Reviews</h1><div id="cell">
    """

    tab_patchlog = """
    <div class="tabs">
    <div class="tab">
    <input type="radio" href="#tab5" id="tab-5" name="tab-group-2">
    <label for="tab-5">Patch Log</label>
    <div class="content">
    """
    patchlog_html = HTML.Table(header_row=['Patch ID', 'Bug ID', 'Flag', 'Flag Setter', 'Last Touched'])
    for row in sorted(patchlog, key=lambda x: x[4], reverse=True):
        title = {}
        if row[5]:
            title["title"] = row[5]
        r = HTML.TableRow(row[:5], attribs=title)
        patchlog_html.rows.append(r)
    content_patchlog = str(patchlog_html)
    close_patchlog = "</div></div>"             # content, tab-9

    tab_reviews = """
    <div class="tab">
    <input type="radio" href="#tab6" id="tab-6" name="tab-group-2" checked>
    <label for="tab-6">Reviews</label>
    <div class="content">
    """
    reviews_html = HTML.Table(header_row=['Patch ID', 'Bug ID', 'Flag', 'Requester', 'Last Touched'])
    for row in sorted(reviews, key=lambda x: x[4], reverse=True):
        title = {}
        color = None
        if row[5]:
            title["title"] = row[5]
        if row[2] == 'review?':
            color = '#FFCCCC'
        r = HTML.TableRow(row[:5], attribs=title, bgcolor=color)
        reviews_html.rows.append(r)
    content_reviews = str(reviews_html)
    close_reviews = "</div></div>"              # content, tab-5

    close_patches = "</div></div></div></div>"  # tabs, cell, box-2, column

    # Build an HTML content
    return main + tab_issues + tab_activity + content_activity + close_activity + \
           tab_assigned + content_assigned + close_assigned + \
           tab_reported + content_reported + close_reported + \
           tab_cc + content_cc + close_cc + \
           close_issues + \
           tab_patches + tab_patchlog + content_patchlog + close_patchlog + \
           tab_reviews + content_reviews + close_reviews + \
           close_patches


def ConvertToTimestamp(date):
    return calendar.timegm(date.timetuple()) * 1000


def Search(server_url, query):
    response = requests.post(server_url + "/_search", query)
    details = CNV.JSON2object(response.content)
    return details


def ConvertToTooltipString(changes):
    if changes:
        tooltip_text = ""
        for change in changes:
            s = Template("[${field_name}(${old_value}->${new_value}]")
            if len(tooltip_text) > 0:
                tooltip_text += "<br>"
            tooltip_text += s.substitute(field_name=change.field_name, old_value=change.old_value, new_value=change.new_value)
        return tooltip_text
    else:
        return ""


if __name__ == "__main__":
    main()
