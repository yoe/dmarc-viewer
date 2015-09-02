from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.contrib.gis.db import models
import choices

############################
"""
DMARC AGGREGATE REPORT MODEL
"""
############################

class Reporter(models.Model):
    org_name                = models.CharField(max_length = 100)
    email                   = models.EmailField()
    extra_contact_info      = models.CharField(max_length = 200, null = True)

    def __unicode__(self):
        return self.org_name

class Report(models.Model):
    """In the Schema a report is called feedback"""
    # Custom field to easily differ between incoming and outgoing
    report_type             = models.IntegerField(choices = choices.REPORT_TYPE)
    date_created            = models.DateTimeField(auto_now = False, auto_now_add = True)
    
    # Meta Data 
    report_id               = models.CharField(max_length = 200, unique = True)
    date_range_begin        = models.DateTimeField()
    date_range_end          = models.DateTimeField()

    version                 = models.DecimalField(max_digits = 4, decimal_places = 2, null = True)
    reporter                = models.ForeignKey('Reporter')

    # Policy Published
    domain                  = models.CharField(max_length = 100)
    adkim                   = models.IntegerField(choices = choices.ALIGNMENT_MODE, null = True)
    aspf                    = models.IntegerField(choices = choices.ALIGNMENT_MODE, null = True)
    p                       = models.IntegerField(choices = choices.DISPOSITION_TYPE)
    sp                      = models.IntegerField(choices = choices.DISPOSITION_TYPE, null = True)
    pct                     = models.IntegerField(null = True)
    fo                      = models.CharField(max_length = 8, null = True)

class ReportError(models.Model):
    report                  = models.ForeignKey('Report')
    error                   = models.CharField(max_length = 200)

class Record(models.Model):
    report                  = models.ForeignKey('Report')

    # Row
    source_ip               = models.GenericIPAddressField()
    geometry                = models.PointField(srid=4326, null = True)
    objects                 = models.GeoManager()

    count                   = models.IntegerField()

    # Policy Evaluated
    disposition             = models.IntegerField(choices = choices.DISPOSITION_TYPE)
    dkim                    = models.IntegerField(choices = choices.DMARC_RESULT)
    spf                     = models.IntegerField(choices = choices.DMARC_RESULT)

    # Identifiers
    envelope_to             = models.CharField(max_length = 100, null = True)
    envelope_from           = models.CharField(max_length = 100, null = True)
    header_from             = models.CharField(max_length = 100, null = True)

class PolicyOverrideReason(models.Model):
    record                  = models.ForeignKey('Record')
    reason_type             = models.IntegerField(choices = choices.POLICY_REASON_TYPE, null = True)
    reason_comment          = models.CharField(max_length = 200, null = True)

class AuthResultDKIM(models.Model):
    record                  = models.ForeignKey('Record')
    domain                  = models.CharField(max_length = 100)
    result                  = models.IntegerField(choices = choices.DKIM_RESULT)
    human_result            = models.CharField(max_length = 200, null = True)

class AuthResultSPF(models.Model):
    record                  = models.ForeignKey('Record')
    domain                  = models.CharField(max_length = 100)
    scope                   = models.IntegerField(choices = choices.SPF_SCOPE, null = True)
    result                  = models.IntegerField(choices = choices.SPF_RESULT)

############################
"""
MYDMARC VIEW/FILTER MODEL
"""
############################

class View(models.Model):
    title                   = models.CharField(max_length = 100)
    description             = models.TextField(null = True)
    enabled                 = models.BooleanField(default = True)
    report_type             = models.IntegerField(choices = choices.REPORT_TYPE)
    
class FilterSet(models.Model):
    view                    = models.ForeignKey('View')
    label                   = models.CharField(max_length = 100)
    color                   = models.CharField(max_length = 7)
    multiple_dkim           = models.NullBooleanField()


class FilterField(models.Model):
    class Meta:
        abstract = True
    def filter(self):
        key = self.report_field.replace('.', "__")
        return "%s=%r" % (key, self.value)

class FilterSetFilterField(FilterField):
    foreign_key             = models.ForeignKey('FilterSet')
    class Meta:
        abstract = True

class ViewFilterField(FilterField):
    foreign_key             = models.OneToOneField(View)
    class Meta:
        abstract = True

class TimeFixed(ViewFilterField):
    # max one per view
    # either time fixed or time variable
    date_range_begin        = models.DateTimeField()
    date_range_end          = models.DateTimeField()

    def filter(self):
        return "date_range_begin__gte= %s, date_range_begin__lte= %s)" \
                % (self.date_range_begin, self.date_range_end)

class TimeVariable(ViewFilterField):
    # Creates period for last <quantity> <unit>
    # needs method that clacs date_range_begin and date_range_end
    # max one per view
    # either time fixed or time variable
    unit                    = models.IntegerField(choices = choices.TIME_UNIT)
    quantity                = models.IntegerField()
    def filter(self):
        end     = datetime.now()
        if (unit == choices.TIME_UNIT_DAY):
            begin = end - relativedelta(days=self.quantity)
        elif (unit == choices.TIME_UNIT_WEEK):
            begin = end - relativedelta(weeks=self.quantity)
        elif (unit == choices.TIME_UNIT_MONTH):
            begin = end - relativedelta(months=self.quantity)
        elif (unit == choices.TIME_UNIT_YEAR):
            begin = end - relativedelta(years=self.quantity)
        else:
            raise #Raise proper Exception

        return "date_range_begin__gte= %s, date_range_begin__lte= %s)" \
                % (begin, end)

class ReportSender(FilterSetFilterField):
    report_field            = "Reporter.email"
    value                   = models.CharField(max_length = 100)

class ReportReceiverDomain(FilterSetFilterField):
    report_field            = "domain"
    value                   = models.CharField(max_length = 100)

class SourceIP(FilterSetFilterField):
    """let's start with simple IP address filtering 
    and maybe consider CIDR notation later"""
    report_field            = "Record.source_ip"
    value                   = models.GenericIPAddressField()

class RawDkimDomain(FilterSetFilterField):
    report_field            = "Record.AuthResultDKIM.domain"
    value                   = models.CharField(max_length = 100)

class RawDkimResult(FilterSetFilterField):
    report_field            = "Record.AuthResultDKIM.result"
    value                   = models.IntegerField(choices = choices.DKIM_RESULT)

class RawSpfDomain(FilterSetFilterField):
    report_field            = "Record.AuthResultSPF.domain"
    value                   = models.CharField(max_length = 100)

class RawSpfResult(FilterSetFilterField):
    report_field            = "Record.AuthResultSPF.result"
    value                   = models.IntegerField(choices = choices.SPF_RESULT)

class AlignedDkimResult(FilterSetFilterField):
    report_field            = "Record.dkim"
    value                   = models.IntegerField(choices = choices.DMARC_RESULT)

class AlignedSpfResult(FilterSetFilterField):
    report_field            = "Record.spf"
    value                   = models.IntegerField(choices = choices.DMARC_RESULT)

class Disposition(FilterSetFilterField):
    report_field            = "Record.disposition"
    value                   = models.IntegerField(choices = choices.DISPOSITION_TYPE)