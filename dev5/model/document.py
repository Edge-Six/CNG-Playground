#!/usr/bin/python
################################################################################
# DOCUMENT
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 11/01/2016 Original construction
################################################################################

import sqlite3
import pickle

from .utils import sucky_uuid

class Document:
    def __init__(self):
        self.connection = sqlite3.connect("db.sqlite", 300)
        self.cursor = self.connection.cursor()

        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.connection.commit()
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TBL_JSON_COL (
                               COLUUID VARCHAR(36),
                               NAME VARCHAR(64) UNIQUE NOT NULL,
                               PRIMARY KEY (COLUUID));''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TBL_JSON_OBJ (
                               OBJUUID VARCHAR(36),
                               COLUUID VARCHAR(36),
                               VALUE BLOB NOT NULL,
                               PRIMARY KEY (OBJUUID),
                               FOREIGN KEY (COLUUID) REFERENCES TBL_JSON_COL(COLUUID) ON DELETE CASCADE);''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TBL_JSON_ATTR (
                               COLUUID VARCHAR(36),
                               ATTRIBUTE VARCHAR(64),
                               PATH VARCHAR(64),
                               PRIMARY KEY (COLUUID, ATTRIBUTE),
                               FOREIGN KEY (COLUUID) REFERENCES TBL_JSON_COL(COLUUID) ON DELETE CASCADE);''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TBL_JSON_IDX (
                               OBJUUID VARCHAR(36),
                               COLUUID VARCHAR(36),
                               ATTRIBUTE VARCHAR(64),
                               VALUE VARCHAR(64),
                               PRIMARY KEY (OBJUUID, ATTRIBUTE),
                               FOREIGN KEY (OBJUUID) REFERENCES TBL_JSON_OBJ(OBJUUID) ON DELETE CASCADE,
                               FOREIGN KEY (COLUUID, ATTRIBUTE) REFERENCES TBL_JSON_ATTR(COLUUID, ATTRIBUTE) ON DELETE CASCADE);''')
        
        self.connection.commit()
        
    def create_object(self, coluuid, objuuid):
        self.cursor.execute("insert into TBL_JSON_OBJ (COLUUID, OBJUUID, VALUE) values (?, ?, ?);", \
                            (str(coluuid), str(objuuid), pickle.dumps({})))
        self.connection.commit()
    
    def set_object(self, coluuid, objuuid, object):
        self.cursor.execute("update TBL_JSON_OBJ set VALUE = ? where OBJUUID = ?;", \
                            (pickle.dumps(object), str(objuuid)))
        self.connection.commit()
        self.index_object(coluuid, objuuid)
    
    def index_object(self, coluuid, objuuid):
        self.cursor.execute("delete from TBL_JSON_IDX where OBJUUID = ?;", (objuuid,))
        self.connection.commit()
        
        attributes = self.list_attributes(coluuid)
        for attribute_name in attributes:
            try:
                self.cursor.execute("""insert into TBL_JSON_IDX (OBJUUID, COLUUID, ATTRIBUTE, VALUE) 
                                    values (?, ?, ?, ?);""", \
                                    (str(objuuid), \
                                     str(coluuid), \
                                     str(attribute_name), \
                                     str(eval("self.get_object(objuuid)" + attributes[attribute_name]))))
                self.connection.commit()
            except Exception as e:
                print str(e)
    
    def get_object(self, objuuid):
        self.cursor.execute("select VALUE from TBL_JSON_OBJ where OBJUUID = ?;", (str(objuuid),))
        self.connection.commit()
        return pickle.loads(self.cursor.fetchall()[0][0])
    
    def find_objects(self, attribute, value):
        self.cursor.execute("select OBJUUID from TBL_JSON_IDX where ATTRIBUTE = ? and VALUE = ?;", \
                            (str(attribute), str(value)))
        self.connection.commit()
        objuuids = []
        for row in self.cursor.fetchall():
            objuuids.append(row[0])
        return objuuids
    
    def delete_object(self, objuuid):
        self.cursor.execute("delete from TBL_JSON_OBJ where OBJUUID = ?;", (str(objuuid),))
        self.connection.commit()
    
    def create_attribute(self, coluuid, attribute, path):
        self.cursor.execute("insert into TBL_JSON_ATTR (COLUUID, ATTRIBUTE, PATH) values (?, ?, ?);", \
                            (str(coluuid), str(attribute), str(path)))
        self.connection.commit()
        
        self.cursor.execute("delete from TBL_JSON_IDX where ATTRIBUTE = ?;", (str(attribute),))
        self.connection.commit()
        
        self.cursor.execute("select OBJUUID, VALUE from TBL_JSON_OBJ where COLUUID = ?;", (str(coluuid),))
        self.connection.commit()
        objects = {}
        for row in self.cursor.fetchall():
            objects[row[0]] = pickle.loads(row[1])
        
        for objuuid in objects:
            try:
                self.cursor.execute("""insert into TBL_JSON_IDX (OBJUUID, COLUUID, ATTRIBUTE, VALUE) 
                                    values (?, ?, ?, ?);""", \
                                    (str(objuuid), \
                                     str(coluuid), \
                                     str(attribute), \
                                     str(eval("objects[objuuid]" + path))))
            except Exception as e:
                print str(e)
            
        self.connection.commit()
    
    def delete_attribute(self, coluuid, attribute):
        self.cursor.execute("delete from TBL_JSON_ATTR where COLUUID = ? and ATTRIBUTE = ?;", \
                            (str(coluuid), str(attribute)))
        self.connection.commit()
        
    def list_attributes(self, coluuid):
        self.cursor.execute("select ATTRIBUTE, PATH from TBL_JSON_ATTR where COLUUID = ?;", (str(coluuid),))
        self.connection.commit()
        
        attributes = {}
        for row in self.cursor.fetchall():
            attributes[row[0]] = row[1]
        return attributes
    
    def create_collection(self, uuid = None, name = "New Collection"):
        if not uuid:
            uuid = sucky_uuid()
            
        self.cursor.execute("insert into TBL_JSON_COL (COLUUID, NAME) values (?, ?);", \
                            (str(uuid), str(name)))
        self.connection.commit()
        return uuid
    
    def delete_collection(self, uuid):
        self.cursor.execute("delete from TBL_JSON_COL where COLUUID = ?;", (str(uuid),))
        self.connection.commit()
    
    def rename_collection(self, uuid, name):
        self.cursor.execute("update TBL_JSON_COL set NAME = ? where COLUUID = ?;", \
                            (str(name), str(uuid)))
        self.connection.commit()
    
    def list_collections(self):
        self.cursor.execute("select NAME, COLUUID from TBL_JSON_COL;")
        self.connection.commit()
            
        collections = {}
        for row in self.cursor.fetchall():
            collections[row[0]] = row[1]
        return collections
    
    def list_collection_objects(self, coluuid):
        self.cursor.execute("select OBJUUID from TBL_JSON_OBJ where COLUUID = ?;", (coluuid,))
        self.connection.commit()
            
        objuuids = []
        for row in self.cursor.fetchall():
            objuuids.append(row[0])
        return objuuids
    
    def __del__(self):
        self.connection.close()

class Object(Document):
    def __init__(self, coluuid, objuuid):
        Document.__init__(self)
        
        self.objuuid = objuuid
        self.coluuid = coluuid
        self.load()
    
    def load(self):
        try:
            self.object = Document.get_object(self, self.objuuid)
        except IndexError:
            Document.create_object(self, self.coluuid, self.objuuid)
            self.object = Document.get_object(self, self.objuuid)
    
    def set(self):
        Document.set_object(self, self.coluuid, self.objuuid, self.object)
    
    def destroy(self):
        Document.delete_object(self, self.objuuid)
        self.object = None
    
    def __del__(self):
        if self.object:
            self.set()
        
class Collection(Document):
    def __init__(self, collection_name):
        Document.__init__(self)
        self.collection_name = collection_name
        
        try:
            self.coluuid = Document.list_collections(self)[self.collection_name]
        except KeyError:
            self.coluuid = Document.create_collection(self, name = self.collection_name)

    def destroy(self):
        Document.delete_collection(self, self.coluuid)
    
    def rename(self, name):
        Document.rename_collection(self, self.coluuid, name)
        self.collection_name = name
    
    def create_attribute(self, attribute, path):
        Document.create_attribute(self, self.coluuid, attribute, path)
    
    def delete_attribute(self, attribute):
        Document.delete_attribute(self, self.coluuid, attribute)
    
    def find(self, **kargs):
        objuuid_sets = []
        for attribute, value in kargs.iteritems():
            objuuid_sets.append(Document.find_objects(self, attribute, value))
        
        intersection = set(objuuid_sets[0])
        for objuuids in objuuid_sets[1:]:
            intersection = intersection.intersection(set(objuuids))
        
        objects = []
        for objuuid in list(intersection):
            objects.append(Object(self.coluuid, objuuid))
        
        return objects

    def get_object(self, objuuid = None):
        if not objuuid:
            objuuid = sucky_uuid()
        return Object(self.coluuid, objuuid)
