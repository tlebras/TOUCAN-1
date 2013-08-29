# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Campaign'
        db.create_table('Mermaid2_db_campaign', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('Mermaid2_db', ['Campaign'])

        # Adding model 'Deployment'
        db.create_table('Mermaid2_db_deployment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('pi', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Mermaid2_db.Campaign'])),
        ))
        db.send_create_signal('Mermaid2_db', ['Deployment'])

        # Adding model 'Point'
        db.create_table('Mermaid2_db_point', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('matchup_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('point', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('time_is', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('pqc', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('mqc', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('land_dist_is', self.gf('django.db.models.fields.FloatField')()),
            ('thetas_is', self.gf('django.db.models.fields.FloatField')()),
            ('deployment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Mermaid2_db.Deployment'])),
        ))
        db.send_create_signal('Mermaid2_db', ['Point'])

        # Adding model 'Instrument'
        db.create_table('Mermaid2_db_instrument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('Mermaid2_db', ['Instrument'])

        # Adding model 'MeasurementType'
        db.create_table('Mermaid2_db_measurementtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('units', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('Mermaid2_db', ['MeasurementType'])

        # Adding model 'MeasurementWavelength'
        db.create_table('Mermaid2_db_measurementwavelength', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('wavelength', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('Mermaid2_db', ['MeasurementWavelength'])

        # Adding model 'Measurement'
        db.create_table('Mermaid2_db_measurement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('measurement_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Mermaid2_db.MeasurementType'])),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Mermaid2_db.Point'])),
            ('wavelength', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Mermaid2_db.MeasurementWavelength'], null=True, blank=True)),
            ('instrument', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Mermaid2_db.Instrument'])),
        ))
        db.send_create_signal('Mermaid2_db', ['Measurement'])

        # Adding model 'InstrumentWavelength'
        db.create_table('Mermaid2_db_instrumentwavelength', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('instrument', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Mermaid2_db.Instrument'])),
        ))
        db.send_create_signal('Mermaid2_db', ['InstrumentWavelength'])

        # Adding model 'Image'
        db.create_table('Mermaid2_db_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('web_location', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archive_location', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('top_left_point', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('bot_right_point', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('instrument', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Mermaid2_db.Instrument'], null=True, blank=True)),
        ))
        db.send_create_signal('Mermaid2_db', ['Image'])


    def backwards(self, orm):
        # Deleting model 'Campaign'
        db.delete_table('Mermaid2_db_campaign')

        # Deleting model 'Deployment'
        db.delete_table('Mermaid2_db_deployment')

        # Deleting model 'Point'
        db.delete_table('Mermaid2_db_point')

        # Deleting model 'Instrument'
        db.delete_table('Mermaid2_db_instrument')

        # Deleting model 'MeasurementType'
        db.delete_table('Mermaid2_db_measurementtype')

        # Deleting model 'MeasurementWavelength'
        db.delete_table('Mermaid2_db_measurementwavelength')

        # Deleting model 'Measurement'
        db.delete_table('Mermaid2_db_measurement')

        # Deleting model 'InstrumentWavelength'
        db.delete_table('Mermaid2_db_instrumentwavelength')

        # Deleting model 'Image'
        db.delete_table('Mermaid2_db_image')


    models = {
        'Mermaid2_db.campaign': {
            'Meta': {'object_name': 'Campaign'},
            'campaign': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'Mermaid2_db.deployment': {
            'Meta': {'object_name': 'Deployment'},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Mermaid2_db.Campaign']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pi': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'Mermaid2_db.image': {
            'Meta': {'object_name': 'Image'},
            'archive_location': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'bot_right_point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Mermaid2_db.Instrument']", 'null': 'True', 'blank': 'True'}),
            'top_left_point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'web_location': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'Mermaid2_db.instrument': {
            'Meta': {'object_name': 'Instrument'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'Mermaid2_db.instrumentwavelength': {
            'Meta': {'object_name': 'InstrumentWavelength'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Mermaid2_db.Instrument']"}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'Mermaid2_db.measurement': {
            'Meta': {'object_name': 'Measurement'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Mermaid2_db.Instrument']"}),
            'measurement_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Mermaid2_db.MeasurementType']"}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Mermaid2_db.Point']"}),
            'value': ('django.db.models.fields.FloatField', [], {}),
            'wavelength': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Mermaid2_db.MeasurementWavelength']", 'null': 'True', 'blank': 'True'})
        },
        'Mermaid2_db.measurementtype': {
            'Meta': {'object_name': 'MeasurementType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'Mermaid2_db.measurementwavelength': {
            'Meta': {'object_name': 'MeasurementWavelength'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'wavelength': ('django.db.models.fields.FloatField', [], {})
        },
        'Mermaid2_db.point': {
            'Meta': {'object_name': 'Point'},
            'deployment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Mermaid2_db.Deployment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'land_dist_is': ('django.db.models.fields.FloatField', [], {}),
            'matchup_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mqc': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'pqc': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'thetas_is': ('django.db.models.fields.FloatField', [], {}),
            'time_is': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['Mermaid2_db']