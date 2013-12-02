# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TriggerResult'
        db.create_table('djtriggers_triggerresult', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('trigger', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['djtriggers.Trigger'])),
            ('result', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('djtriggers', ['TriggerResult'])


    def backwards(self, orm):
        # Deleting model 'TriggerResult'
        db.delete_table('djtriggers_triggerresult')


    models = {
        'djtriggers.trigger': {
            'Meta': {'object_name': 'Trigger'},
            'date_processed': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date_received': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'process_after': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'trigger_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'djtriggers.triggerresult': {
            'Meta': {'object_name': 'TriggerResult'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.TextField', [], {}),
            'trigger': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['djtriggers.Trigger']"})
        }
    }

    complete_apps = ['djtriggers']