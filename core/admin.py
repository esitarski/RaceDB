from django.contrib import admin
from models import *

# Register your models here.
admin.site.register( CategoryFormat )
admin.site.register( Category )
admin.site.register( Competition )

admin.site.register( Wave )
admin.site.register( WaveCallup )

admin.site.register( Team )
admin.site.register( LicenseHolder )
admin.site.register( Participant )

#admin.site.register( EventTimeTrial )

#admin.site.register( PenaltyClass )
#admin.site.register( PenaltyTemplate )
#admin.site.register( Penalty )

#admin.site.register( MassStartEntry )
#admin.site.register( TimeTrialEntry )

#admin.site.register( KOMPoints )
#admin.site.register( KOMPointsResult )

#admin.site.register( SprintPoints )
#admin.site.register( SprintPointsResult )

#admin.site.register( TimeBonus )
#admin.site.register( Observation )
