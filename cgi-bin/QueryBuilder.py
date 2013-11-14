from string import Template


class QueryBuilder:
    @staticmethod
    def SubmittedBugs(username, start_ts, end_ts, current_ts):
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"term":{"bug_version.created_by":"${username}"}},
                                {"range":{"bug_version.modified_ts":{"gte":"${start}","lte":"${end}"}}},
                                {"or":[
                                  {"range":{"expires_on":{"gt":${current_time}}}},
                                  {"missing":{"field":"expires_on"}}
                                ]}
                              ]}
                            }
                          },
                          "from":0,
                          "size":200000,
                          "sort":[],
                          "facets":{},
                          "fields":["bug_id", "short_desc", "modified_ts", "changes"]
                        }""")
        return s.substitute(username=username, start=start_ts, end=end_ts, current_time=current_ts)

    @staticmethod
    def AssignedBugs(username, start_ts, end_ts, current_ts):
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"term":{"bug_version.assigned_to":"${username}"}},
                                {"range":{"bug_version.modified_ts":{"gte":"${start}","lte":"${end}"}}},
                                {"or":[
                                  {"range":{"expires_on":{"gt":${current_time}}}},
                                  {"missing":{"field":"expires_on"}}
                                ]}
                              ]}
                            }
                          },
                          "from":0,
                          "size":200000,
                          "sort":[],
                          "facets":{},
                          "fields":["bug_id", "short_desc", "modified_ts", "changes"]
                        }""")
        return s.substitute(username=username, start=start_ts, end=end_ts, current_time=current_ts)

    @staticmethod
    def CC(username, start_ts, end_ts, current_ts):
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"term":{"bug_version.cc":"${username}"}},
                                {"range":{"bug_version.modified_ts":{"gte":"${start}","lte":"${end}"}}},
                                {"or":[
                                  {"range":{"expires_on":{"gt":${current_time}}}},
                                  {"missing":{"field":"expires_on"}}
                                ]}
                              ]}
                            }
                          },
                          "from":0,
                          "size":200000,
                          "sort":[],
                          "facets":{},
                          "fields":["bug_id", "short_desc", "modified_ts", "changes"]
                        }""")
        return s.substitute(username=username, start=start_ts, end=end_ts, current_time=current_ts)

    @staticmethod
    def BugsWithCommentsFromUser(username, start_ts):
        """
        Prepare the query that will produce a list of bug_ids for the bugs that have comments
        from the user created after the specified timestamp
        The output of the query might contain duplicate ids, therefore post-processing is required
        :param username:
        :param start_ts: timestamp that is used to filter the list of comments
        :return:
        """
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"term":{"modified_by":"${username}"}},
                                {"range":{"modified_ts":{"gte":"${start}"}}}
                              ]}
                            }
                          },
                          "from":0,
                          "size":200000,
                          "sort":[],
                          "facets":{},
                          "fields":["bug_id"]
                        }""")
        return s.substitute(username=username, start=start_ts)

    @staticmethod
    def MinCreatedTimestamp(start_ts, end_ts, current_ts):
        """
        Prepare the query that will return the min 'created_ts' for bugs with the last document changed during a specified period.
        :param start_ts: the beginning of the period
        :param end_ts: the end of the period
        :param current_ts:
        :return:
        """
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"range":{"bug_version.modified_ts":{"gte":"${start}","lte":"${end}"}}},
                                {"or":[
                                  {"range":{"expires_on":{"gt":${current_time}}}},
                                  {"missing":{"field":"expires_on"}}
                                ]}
                              ]}
                            }
                          },
                          "from":0,
                          "size":1,
                          "sort":["created_ts"],
                          "facets":{},
                          "fields":["created_ts"]
                        }""")
        return s.substitute(start=start_ts, end=end_ts, current_time=current_ts)

    @staticmethod
    def BugsForThePeriod(start_ts, end_ts, current_ts, bug_filter):
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"range":{"bug_version.modified_ts":{"gte":"${start}","lte":"${end}"}}},
                                {"or":[
                                  {"range":{"expires_on":{"gt":${current_time}}}},
                                  {"missing":{"field":"expires_on"}}
                                ]},
                                {"terms":{"bug_id" : ${bug_id_filter}}}
                              ]}
                            }
                          },
                          "from":0,
                          "size":200000,
                          "sort":[],
                          "facets":{},
                          "fields":["bug_id", "short_desc", "modified_ts", "changes"]
                        }""")
        return s.substitute(start=start_ts, end=end_ts, current_time=current_ts, bug_id_filter=bug_filter)

    @staticmethod
    def PatchLog(username, start_ts, end_ts, current_ts):
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"range":{"bug_version.modified_ts":{"gte":"${start}","lte":"${end}"}}},
                                {"nested": {
                                    "path" : "attachments",
                                    "query": {
                                        "filtered" : {
                                            "query" : {
                                                "match_all" : {}
                                            },
                                            "filter" : {
                                                "and":[
                                                    {"exists":{"field":"attachments.created_by"}},
                                                    {"term" : {"attachments.created_by" : "${username}"}}
                                                ]
                                            }
                                        }
                                    }
                                }},
                                {"or":[
                                  {"range":{"expires_on":{"gt":${current_time}}}},
                                  {"missing":{"field":"expires_on"}}
                                ]}
                              ]}
                            }
                          },
                          "from":0,
                          "size":200000,
                          "sort":[],
                          "facets":{},
                          "fields" : ["bug_id", "attachments", "modified_ts", "changes"]
                        }""")
        return s.substitute(username=username, start=start_ts, end=end_ts, current_time=current_ts)

    @staticmethod
    def FinishedReviews(username, start_ts, end_ts, current_ts):
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"range":{"bug_version.modified_ts":{"gte":"${start}","lte":"${end}"}}},
                                {"nested": {
                                    "path" : "attachments.flags",
                                    "query": {
                                        "filtered" : {
                                            "query" : {
                                                "match_all" : {}
                                            },
                                            "filter" : {
                                                "and":[
                                                    {"exists": {"field":"attachments.flags.modified_by"}},
                                                    {"exists": {"field":"attachments.flags.request_status"}},
                                                    {"exists": {"field":"attachments.flags.request_type"}},
                                                    {"term"  : {"attachments.flags.modified_by" : "${username}"}},
                                                    {"terms" : {"attachments.flags.request_type":["review","superreview"]}},
                                                    {"terms" : {"attachments.flags.request_status":["+", "-"]}}
                                                ]
                                            }
                                        }
                                    }
                                }},
                                {"or":[
                                  {"range":{"expires_on":{"gt":${current_time}}}},
                                  {"missing":{"field":"expires_on"}}
                                ]}
                              ]}
                            }
                          },
                          "from":0,
                          "size":200000,
                          "sort":[],
                          "facets":{},
                          "fields" : ["bug_id", "attachments", "modified_ts", "changes"]
                        }""")
        return s.substitute(username=username, start=start_ts, end=end_ts, current_time=current_ts)

    @staticmethod
    def PendingReviews(username, current_ts):
        s = Template("""{
                         "query":
                          {"filtered":
                            {"query":
                              {"match_all":{}},
                              "filter":{"and":[
                                {"nested": {
                                    "path" : "attachments.flags",
                                    "query": {
                                        "filtered" : {
                                            "query" : {
                                                "match_all" : {}
                                            },
                                            "filter" : {
                                                "and":[
                                                    {"exists": {"field":"attachments.flags.requestee"}},
                                                    {"exists": {"field":"attachments.flags.request_status"}},
                                                    {"exists": {"field":"attachments.flags.request_type"}},
                                                    {"term"  : {"attachments.flags.requestee" : "${username}"}},
                                                    {"terms" : {"attachments.flags.request_type":["review","superreview"]}},
                                                    {"term"  : {"attachments.flags.request_status": "?"}}
                                                ]
                                            }
                                        }
                                    }
                                }},
                                {"or":[
                                  {"range":{"expires_on":{"gt":${current_time}}}},
                                  {"missing":{"field":"expires_on"}}
                                ]}
                              ]}
                            }
                          },
                          "from":0,
                          "size":200000,
                          "sort":[],
                          "facets":{},
                          "fields" : ["bug_id", "attachments", "modified_ts", "changes"]
                        }""")
        return s.substitute(username=username, current_time=current_ts)
