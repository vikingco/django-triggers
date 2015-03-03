# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'Trigger', fields ['source']
        db.delete_unique('djtriggers_trigger', ['source'])


    def backwards(self, orm):
        
        # Adding unique constraint on 'Trigger', fields ['source']
        db.create_unique('djtriggers_trigger', ['source'])


    models = {
        'djtriggers.trigger': {
            'Meta': {'object_name': 'Trigger'},
            'date_processed': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date_received': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'process_after': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'trigger_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['djtriggers']
