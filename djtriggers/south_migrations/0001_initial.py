# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Trigger'
        db.create_table('djtriggers_trigger', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('trigger_type', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=250, unique=True, null=True, blank=True)),
            ('date_received', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_processed', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('process_after', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal('djtriggers', ['Trigger'])


    def backwards(self, orm):
        
        # Deleting model 'Trigger'
        db.delete_table('djtriggers_trigger')


    models = {
        'djtriggers.trigger': {
            'Meta': {'object_name': 'Trigger'},
            'date_processed': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date_received': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'process_after': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'trigger_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['djtriggers']
