# vim: set sw=4 et:

import logging
import brozzler
import rethinkdb
r = rethinkdb
import random

class UnexpectedDbResult(Exception):
    pass

class BrozzlerRethinkDb:
    logger = logging.getLogger(__module__ + "." + __qualname__)

    def __init__(self, servers=["localhost"], db="brozzler", shards=3, replicas=3):
        self.servers = servers
        self.db = db
        self.shards = shards
        self.replicas = replicas
        self._ensure_db()

    # https://github.com/rethinkdb/rethinkdb-example-webpy-blog/blob/master/model.py
    # "Best practices: Managing connections: a connection per request"
    def _random_server_connection(self):
        server = random.choice(self.servers)
        try:
            host, port = server.split(":")
            return r.connect(host=host, port=port)
        except ValueError:
            return r.connect(host=server)

    def _ensure_db(self):
        with self._random_server_connection() as conn:
            try:
                tables = r.db(self.db).table_list().run(conn)
                for tbl in "sites", "pages":
                    if not tbl in tables:
                        raise Exception("rethinkdb database {} exists but does not have table {}".format(repr(self.db), repr(tbl)))
            except rethinkdb.errors.ReqlOpFailedError as e:
                self.logger.info("rethinkdb database %s does not exist, initializing", repr(self.db))
                r.db_create(self.db).run(conn)
                # r.db("test").table_create("jobs", shards=self.shards, replicas=self.replicas).run(conn)
                r.db(self.db).table_create("sites", shards=self.shards, replicas=self.replicas).run(conn)
                r.db(self.db).table_create("pages", shards=self.shards, replicas=self.replicas).run(conn)
                r.db(self.db).table("pages").index_create("priority_by_site", [r.row["site_id"], r.row["claimed"], r.row["brozzle_count"], r.row["priority"]]).run(conn)
                self.logger.info("created database %s with tables 'sites' and 'pages'", self.db)

    def _vet_result(self, result, **kwargs):
        self.logger.debug("vetting expected=%s result=%s", kwargs, result)
        # {'replaced': 0, 'errors': 0, 'skipped': 0, 'inserted': 1, 'deleted': 0, 'generated_keys': ['292859c1-4926-4b27-9d87-b2c367667058'], 'unchanged': 0}
        for k in ["replaced", "errors", "skipped", "inserted", "deleted", "unchanged"]:
            if k in kwargs:
                expected = kwargs[k]
            else:
                expected = 0
            if isinstance(expected, list):
                if result.get(k) not in kwargs[k]:
                    raise UnexpectedDbResult("expected {} to be one of {} in {}".format(repr(k), expected, result))
            else:
                if result.get(k) != expected:
                    raise UnexpectedDbResult("expected {} to be {} in {}".format(repr(k), expected, result))

    def new_site(self, site):
        self.logger.info("inserting into 'sites' table %s", site)
        with self._random_server_connection() as conn:
            result = r.db(self.db).table("sites").insert(site.to_dict()).run(conn)
            self._vet_result(result, inserted=1)
            site.id = result["generated_keys"][0]

    def update_site(self, site):
        self.logger.debug("updating 'sites' table entry %s", site)
        with self._random_server_connection() as conn:
            result = r.db(self.db).table("sites").get(site.id).update(site.to_dict()).run(conn)
            self._vet_result(result, replaced=1)

    def update_page(self, page):
        self.logger.debug("updating 'pages' table entry %s", page)
        with self._random_server_connection() as conn:
            result = r.db(self.db).table("pages").get(page.id).update(page.to_dict()).run(conn)
            self._vet_result(result, replaced=[0,1], unchanged=[0,1])

    def new_page(self, page):
        self.logger.debug("inserting into 'pages' table %s", page)
        with self._random_server_connection() as conn:
            result = r.db(self.db).table("pages").insert(page.to_dict()).run(conn)
            self._vet_result(result, inserted=1)

    def claim_site(self):
        # XXX keep track of aggregate priority and prioritize sites accordingly?
        with self._random_server_connection() as conn:
            result = r.db(self.db).table("sites").filter({"claimed":False,"status":"ACTIVE"}).limit(1).update({"claimed":True},return_changes=True).run(conn)
            self._vet_result(result, replaced=[0,1])
            if result["replaced"] == 1:
                return brozzler.Site(**result["changes"][0]["new_val"])
            else:
                raise brozzler.NothingToClaim

    def claim_page(self, site):
        with self._random_server_connection() as conn:
            result = (r.db(self.db).table("pages")
                    .between([site.id,False,0,brozzler.MIN_PRIORITY], [site.id,False,0,brozzler.MAX_PRIORITY], index="priority_by_site")
                    .order_by(index=r.desc("priority_by_site")).limit(1)
                    .update({"claimed":True},return_changes=True).run(conn))
            self._vet_result(result, replaced=[0,1])
            if result["replaced"] == 1:
                return brozzler.Page(**result["changes"][0]["new_val"])
            else:
                raise brozzler.NothingToClaim

    def has_outstanding_pages(self, site):
        with self._random_server_connection() as conn:
            cursor = r.db(self.db).table("pages").between([site.id,False,0,brozzler.MIN_PRIORITY], [site.id,True,0,brozzler.MAX_PRIORITY], index="priority_by_site").limit(1).run(conn)
            return len(list(cursor)) > 0

    def get_page(self, page):
        with self._random_server_connection() as conn:
            result = r.db(self.db).table("pages").get(page.id).run(conn)
            if result:
                return brozzler.Page(**result)
            else:
                return None
