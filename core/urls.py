from django.urls import include, path, re_path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from core import views
from core import participant
from core import self_serve
from core import number_set
from core import seasons_pass
from core import discipline
from core import race_class
from core import report_label
from core import legal_entity
from core import category
from core import category_numbers
from core import team
from core import hub
from core import series
from core import custom_category
from core import callups
from core import custom_label
from core import competition_category_option
from core import competition_found_tag
from core import crossmgr_password
from core import image
from core import gpx_course

import warnings
warnings.simplefilter('error', DeprecationWarning)

urlpatterns = [
	re_path(r'^$', views.home, name='home'),
	re_path(r'^(?P<rfid_antenna>\d+)/$', views.home),
	re_path(r'^Home/$', views.home),
	
	re_path(r'^.*Hub/$', RedirectView.as_view(url='/RaceDB/Hub/SearchCompetitions/')),
	re_path(r'^.*Hub/SearchCompetitions/$', hub.SearchCompetitions),
	re_path(r'^.*Hub/CompetitionResults/(?P<competitionId>\d+)/$', hub.CompetitionResults),
	re_path(r'^.*Hub/CategoryResults/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<categoryId>\d+)/$', hub.CategoryResults),
	re_path(r'^.*Hub/CustomCategoryResults/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<customCategoryId>\d+)/$', hub.CustomCategoryResults),
	re_path(r'^.*EventAnimation/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<categoryId>\d+)/$', hub.EventAnimation),
	re_path(r'^.*EventLapTimes/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<categoryId>\d+)/$', hub.EventLapTimes),
	re_path(r'^.*EventLapChart/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<categoryId>\d+)/$', hub.EventLapChart),
	re_path(r'^.*EventGapChart/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<categoryId>\d+)/$', hub.EventGapChart),
	re_path(r'^.*EventRaceChart/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<categoryId>\d+)/$', hub.EventRaceChart),
	
	re_path(r'^.*Hub/LicenseHolderResults/(?P<licenseHolderId>\d+)/$', hub.LicenseHolderResults),
	re_path(r'^.*Hub/ResultAnalysis/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<resultId>\d+)/$', hub.ResultAnalysis),
	
	re_path(r'^.*Hub/SearchLicenseHolders/$', hub.SearchLicenseHolders),
	
	re_path(r'^.*Hub/Series/$', hub.SeriesList),
	re_path(r'^.*Hub/SeriesCategories/(?P<seriesId>\d+)/$', hub.SeriesCategories),
	re_path(r'^.*Hub/SeriesCategoryResults/(?P<seriesId>\d+)/(?P<categoryId>\d+)/$', hub.SeriesCategoryResults),
	re_path(r'^.*Hub/SeriesCategoryResults/(?P<seriesId>\d+)/(?P<categoryId>\d+)/(?P<customCategoryIndex>\d+)/$', hub.SeriesCategoryResults),
	
	re_path(r'^.*SelfServe/$', self_serve.SelfServe),
	re_path(r'^.*SelfServe/(?P<action>\d+)/$', self_serve.SelfServe),
	re_path(r'^.*SelfServe/4/SelfServeSignature/$', self_serve.SelfServeSignature),
	re_path(r'^.*SelfServe/SelfServeQR/$', self_serve.SelfServeQRCode),
	
	re_path(r'^.*Competitions/$', views.CompetitionsDisplay),
	re_path(r'^.*CompetitionNew/$', views.CompetitionNew),
	re_path(r'^.*CompetitionCopy/(?P<competitionId>\d+)/$', views.CompetitionCopy),
	re_path(r'^.*CompetitionEdit/(?P<competitionId>\d+)/$', views.CompetitionEdit),
	re_path(r'^.*CompetitionExport/(?P<competitionId>\d+)/$', views.CompetitionExport),
	re_path(r'^.*CompetitionImport/$', views.CompetitionImport),
	re_path(r'^.*CompetitionDelete/(?P<competitionId>\d+)/$', views.CompetitionDelete),
	re_path(r'^.*CompetitionDashboard/(?P<competitionId>\d+)/$', views.CompetitionDashboard),
	re_path(r'^.*CompetitionReports/(?P<competitionId>\d+)/$', views.CompetitionReports),
	re_path(r'^.*CompetitionRegAnalytics/(?P<competitionId>\d+)/$', views.CompetitionRegAnalytics),
	re_path(r'^.*CompetitionParticipationSummary/(?P<competitionId>\d+)/$', views.CompetitionParticipationSummary),
	re_path(r'^.*CompetitionApplyOptionalEventChangesToExistingParticipants/(?P<competitionId>\d+)/$', views.CompetitionApplyOptionalEventChangesToExistingParticipants),
	re_path(r'^.*CompetitionApplyOptionalEventChangesToExistingParticipants/(?P<competitionId>\d+)/(?P<confirmed>\d+)/$', views.CompetitionApplyOptionalEventChangesToExistingParticipants),
	re_path(r'^.*TeamsShow/(?P<competitionId>\d+)/$', views.TeamsShow),
	re_path(r'^.*UploadPrereg/(?P<competitionId>\d+)/$', views.UploadPrereg),
	re_path(r'^.*FinishLynx/(?P<competitionId>\d+)/$', views.FinishLynx),
	re_path(r'^.*StartLists/(?P<competitionId>\d+)/$', views.StartLists),
	re_path(r'^.*StartList/(?P<eventId>\d+)/$', views.StartList),
	
	re_path(r'^.*CompetitionCloudUpload/$', views.CompetitionCloudUpload),
	
	re_path(r'^.*ApplyNumberSet/(?P<competitionId>\d+)/$', views.ApplyNumberSet),
	re_path(r'^.*InitializeNumberSet/(?P<competitionId>\d+)/$', views.InitializeNumberSet),
	
	re_path(r'^.*SetLicenseChecks/(?P<competitionId>\d+)/$', competition_category_option.SetLicenseChecks),
	re_path(r'^.*UploadCCOs/(?P<competitionId>\d+)/$', competition_category_option.UploadCCOs),
	
	re_path(r'^.*StartListTT/(?P<eventTTId>\d+)/$', views.StartListTT),
	
	re_path(r'^.*StartListEmails/(?P<eventId>\d+)/(?P<eventType>\d+)/$', views.StartListEmails),
	re_path(r'^.*StartListExcelDownload/(?P<eventId>\d+)/(?P<eventType>\d+)/$', views.StartListExcelDownload),
	
	re_path(r'^.*UCIExcelDownload/(?P<eventId>\d+)/(?P<eventType>\d+)/$', views.UCIExcelDownload),
	re_path(r'^.*UCIExcelDownload/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<startList>\d+)/$', views.UCIExcelDownload),
	
	re_path(r'^.*ParticipantBarcodeAdd/(?P<competitionId>\d+)/$', participant.ParticipantBarcodeAdd),
	re_path(r'^.*ParticipantRfidAdd/(?P<competitionId>\d+)/$', participant.ParticipantRfidAdd),
	re_path(r'^.*ParticipantRfidAdd/(?P<competitionId>\d+)/(?P<autoSubmit>\d+)/$', participant.ParticipantRfidAdd),
	re_path(r'^.*ParticipantBibAdd/(?P<competitionId>\d+)/$', participant.ParticipantBibAdd),
	
	re_path(r'^.*ParticipantsResetBibs/(?P<competitionId>\d+)/$', participant.ParticipantsResetBibs),
	re_path(r'^.*ParticipantsResetBibs/(?P<competitionId>\d+)/(?P<confirmed>\d+)/$', participant.ParticipantsResetBibs),

	re_path(r'^.*ParticipantsResetTags/(?P<competitionId>\d+)/$', participant.ParticipantsResetTags),
	re_path(r'^.*ParticipantsResetTags/(?P<competitionId>\d+)/(?P<confirmed>\d+)/$', participant.ParticipantsResetTags),

	re_path(r'^.*ParticipantTagChangeUSBReader/(?P<participantId>\d+)/$', participant.ParticipantTagChangeUSBReader),
	re_path(r'^.*ParticipantTagChangeUSBReader/(?P<participantId>\d+)/(?P<action>\d+)/$', participant.ParticipantTagChangeUSBReader),
	
	re_path(r'^.*CompetitionFoundTag/(?P<competitionId>\d+)/$', competition_found_tag.CompetitionFoundTag),
	re_path(r'^.*CompetitionFoundTag/(?P<competitionId>\d+)/(?P<rfid_tag>[^/]+)/(?P<action>\d+)/$', competition_found_tag.CompetitionFoundTag),
	
	re_path(r'^.*CategoryNumbers/(?P<competitionId>\d+)/$', category_numbers.CategoryNumbersDisplay),
	re_path(r'^.*CategoryNumbersNew/(?P<competitionId>\d+)/$', category_numbers.CategoryNumbersNew),
	re_path(r'^.*CategoryNumbersEdit/(?P<categoryNumbersId>\d+)/$', category_numbers.CategoryNumbersEdit),
	re_path(r'^.*CategoryNumbersDelete/(?P<categoryNumbersId>\d+)/$', category_numbers.CategoryNumbersDelete),
	
	re_path(r'^.*EventMassStarts/(?P<competitionId>\d+)/$', views.EventMassStartDisplay),
	re_path(r'^.*EventMassStartNew/(?P<competitionId>\d+)/$', views.EventMassStartNew),
	re_path(r'^.*EventMassStartEdit/(?P<eventId>\d+)/$', views.EventMassStartEdit),
	re_path(r'^.*EventMassStartCrossMgr/(?P<eventId>\d+)/$', views.EventMassStartCrossMgr),
	re_path(r'^.*EventMassStartDelete/(?P<eventId>\d+)/$', views.EventMassStartDelete),
	
	re_path(r'^.*UploadCrossMgr/$', views.UploadCrossMgr),
	re_path(r'^.*VerifyCrossMgr/$', views.VerifyCrossMgr),
	
	re_path(r'^.*CustomLabel/(?P<competitionId>\d+)/$', custom_label.CustomLabel),
	
	re_path(r'^.*WaveNew/(?P<eventMassStartId>\d+)/$', views.WaveNew),
	re_path(r'^.*WaveEdit/(?P<waveId>\d+)/$', views.WaveEdit),
	re_path(r'^.*WaveDelete/(?P<waveId>\d+)/$', views.WaveDelete),
	
	re_path(r'^.*EventTTs/(?P<competitionId>\d+)/$', views.EventTTDisplay),
	re_path(r'^.*EventTTNew/(?P<competitionId>\d+)/$', views.EventTTNew),
	re_path(r'^.*EventTTEdit/(?P<eventTTId>\d+)/$', views.EventTTEdit),
	re_path(r'^.*EventTTCrossMgr/(?P<eventTTId>\d+)/$', views.EventTTCrossMgr),
	re_path(r'^.*EventTTDelete/(?P<eventTTId>\d+)/$', views.EventTTDelete),
	
	re_path(r'^.*EventApplyToExistingParticipants/(?P<eventId>\d+)/$', views.EventApplyToExistingParticipants),
	re_path(r'^.*EventApplyToExistingParticipants/(?P<eventId>\d+)/(?P<confirmed>\d+)/$', views.EventApplyToExistingParticipants),
	
	re_path(r'^.*SeedingEdit/(?P<eventTTId>\d+)/$', views.SeedingEdit),
	re_path(r'^.*SeedingEdit/(?P<eventTTId>\d+)/(?P<entry_tt_i>\d+)/$', views.SeedingEdit),
	re_path(r'^.*SeedingEditEntry/(?P<eventTTId>\d+)/(?P<entry_tt_i>\d+)/$', views.SeedingEditEntry),
	re_path(r'^.*GenerateStartTimes/(?P<eventTTId>\d+)/$', views.GenerateStartTimes),
	
	re_path(r'^.*WaveTTNew/(?P<eventTTId>\d+)/$', views.WaveTTNew),
	re_path(r'^.*WaveTTEdit/(?P<waveTTId>\d+)/$', views.WaveTTEdit),
	re_path(r'^.*WaveTTDelete/(?P<waveTTId>\d+)/$', views.WaveTTDelete),
	re_path(r'^.*WaveTTUp/(?P<waveTTId>\d+)/$', views.WaveTTUp),
	re_path(r'^.*WaveTTDown/(?P<waveTTId>\d+)/$', views.WaveTTDown),
	
	re_path(r'^.*Callups/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<seriesId>\d+)/$', callups.Callups),
	
	re_path(r'^.*Participants/(?P<competitionId>\d+)/$', participant.Participants),
	re_path(r'^.*ParticipantsInEvents/(?P<competitionId>\d+)/$', participant.ParticipantsInEvents),
	re_path(r'^.*ParticipantManualAdd/(?P<competitionId>\d+)/$', participant.ParticipantManualAdd),
	re_path(r'^.*ParticipantNotFound/(?P<competitionId>\d+)/$', participant.ParticipantNotFound),
	re_path(r'^.*ParticipantAddToCompetition/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', participant.ParticipantAddToCompetition),
	re_path(r'^.*ParticipantAddToCompetitionDifferentCategory/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$',
				participant.ParticipantAddToCompetitionDifferentCategory),
	re_path(r'^.*ParticipantAddToCompetitionDifferentCategoryConfirm/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$',
				participant.ParticipantAddToCompetitionDifferentCategoryConfirm),
	re_path(r'^.*ParticipantEdit/(?P<participantId>\d+)/$', participant.ParticipantEdit),
	re_path(r'^.*ParticipantEditFromLicenseHolder/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', participant.ParticipantEditFromLicenseHolder),
	re_path(r'^.*ParticipantRemove/(?P<participantId>\d+)/$', participant.ParticipantRemove),
	re_path(r'^.*ParticipantDoDelete/(?P<participantId>\d+)/$', participant.ParticipantDoDelete),
	
	re_path(r'^.*LicenseHolderAddConfirm/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', views.LicenseHolderAddConfirm),
	re_path(r'^.*LicenseHolderConfirmAddToCompetition/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', views.LicenseHolderConfirmAddToCompetition),
	re_path(r'^.*LicenseHolderAddConfirm/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/(?P<tag_checked>\d)/$', views.LicenseHolderAddConfirm),
	re_path(r'^.*LicenseHolderConfirmAddToCompetition/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/(?P<tag_checked>\d)/$',
		views.LicenseHolderConfirmAddToCompetition),
	
	re_path(r'^.*ParticipantCategoryChange/(?P<participantId>\d+)/$', participant.ParticipantCategoryChange ),
	re_path(r'^.*ParticipantCategorySelect/(?P<participantId>\d+)/(?P<categoryId>\d+)/$', participant.ParticipantCategorySelect ),
	
	re_path(r'^.*ParticipantRoleChange/(?P<participantId>\d+)/$', participant.ParticipantRoleChange ),
	re_path(r'^.*ParticipantRoleSelect/(?P<participantId>\d+)/(?P<role>\d+)/$', participant.ParticipantRoleSelect ),
	
	re_path(r'^.*ParticipantConfirmedChange/(?P<participantId>\d+)/$', participant.ParticipantBooleanChange, {'field':'confirmed'}),
	re_path(r'^.*ParticipantPreregisteredChange/(?P<participantId>\d+)/$', participant.ParticipantBooleanChange, {'field':'preregistered'}),
	re_path(r'^.*ParticipantPaidChange/(?P<participantId>\d+)/$', participant.ParticipantBooleanChange, {'field':'paid'}),
	
	re_path(r'^.*ParticipantSignatureChange/(?P<participantId>\d+)/$', participant.ParticipantSignatureChange ),
	re_path(r'^.*SetSignatureWithTouchScreen/(?P<use_touch_screen>\d+)/$', participant.SetSignatureWithTouchScreen ),
	
	re_path(r'^.*ParticipantTeamChange/(?P<participantId>\d+)/$', participant.ParticipantTeamChange ),
	re_path(r'^.*ParticipantTeamSelect/(?P<participantId>\d+)/(?P<teamId>\d+)/$', participant.ParticipantTeamSelect ),
	re_path(r'^.*ParticipantTeamSelectDiscipline/(?P<participantId>\d+)/(?P<teamId>\d+)/$', participant.ParticipantTeamSelectDiscipline ),
	
	re_path(r'^.*LicenseHolderNationCodeChange/(?P<licenseHolderId>\d+)/$', participant.LicenseHolderNationCodeChange ),
	re_path(r'^.*LicenseHolderNationCodeSelect/(?P<licenseHolderId>\d+)/(?P<iocI>\d+)/$', participant.LicenseHolderNationCodeSelect ),
	re_path(r'^.*ParticipantConfirm/(?P<participantId>\d+)/$', participant.ParticipantConfirm ),
	
	re_path(r'^.*ParticipantBibChange/(?P<participantId>\d+)/$', participant.ParticipantBibChange ),
	re_path(r'^.*ParticipantBibSelect/(?P<participantId>\d+)/(?P<bib>\d+)/$', participant.ParticipantBibSelect ),
	
	re_path(r'^.*ParticipantLicenseCheckChange/(?P<participantId>\d+)/$', participant.ParticipantLicenseCheckChange ),
	re_path(r'^.*ParticipantLicenseCheckSelect/(?P<participantId>\d+)/(?P<status>\d+)/$', participant.ParticipantLicenseCheckSelect ),
	
	re_path(r'^.*ParticipantTagChange/(?P<participantId>\d+)/$', participant.ParticipantTagChange ),
	re_path(r'^.*ParticipantNoteChange/(?P<participantId>\d+)/$', participant.ParticipantNoteChange ),
	re_path(r'^.*ParticipantGeneralNoteChange/(?P<participantId>\d+)/$', participant.ParticipantGeneralNoteChange ),
	re_path(r'^.*ParticipantOptionChange/(?P<participantId>\d+)/$', participant.ParticipantOptionChange ),
	re_path(r'^.*ParticipantEstSpeedChange/(?P<participantId>\d+)/$', participant.ParticipantEstSpeedChange ),
	re_path(r'^.*ParticipantWaiverChange/(?P<participantId>\d+)/$', participant.ParticipantWaiverChange ),
	re_path(r'^.*ParticipantPrintBibLabels/(?P<participantId>\d+)/$', participant.ParticipantPrintBibLabels ),
	re_path(r'^.*ParticipantPrintBibLabel1/(?P<participantId>\d+)/$', participant.ParticipantPrintBibLabel1 ),
	re_path(r'^.*ParticipantPrintBodyBib/(?P<participantId>\d+)/$', participant.ParticipantPrintBodyBib ),
	re_path(r'^.*ParticipantPrintBodyBib/(?P<participantId>\d+)/(?P<copies>\d+)/$', participant.ParticipantPrintBodyBib ),
	re_path(r'^.*ParticipantPrintBodyBib/(?P<participantId>\d+)/(?P<copies>\d+)/(?P<onePage>\d+)/$', participant.ParticipantPrintBodyBib ),
	re_path(r'^.*ParticipantPrintShoulderBib/(?P<participantId>\d+)/$', participant.ParticipantPrintShoulderBib ),
	re_path(r'^.*ParticipantPrintAllBib/(?P<participantId>\d+)/$', participant.ParticipantPrintAllBib ),
	re_path(r'^.*ParticipantEmergencyContactInfo/(?P<participantId>\d+)/$', participant.ParticipantEmergencyContactInfo ),
	re_path(r'^.*ParticipantPrintEmergencyContactInfo/(?P<participantId>\d+)/$', participant.ParticipantPrintEmergencyContactInfo ),
	
	re_path(r'^.*LicenseHolders/$', views.LicenseHoldersDisplay),
	re_path(r'^.*LicenseHolderNew/$', views.LicenseHolderNew),
	re_path(r'^.*LicenseHolderBarcodeScan/$', views.LicenseHolderBarcodeScan),
	re_path(r'^.*LicenseHolderRfidScan/$', views.LicenseHolderRfidScan),
	re_path(r'^.*LicenseHolderTagChange/(?P<licenseHolderId>\d+)/$', views.LicenseHolderTagChange),
	re_path(r'^.*LicenseHolderEdit/(?P<licenseHolderId>\d+)/$', views.LicenseHolderEdit),
	re_path(r'^.*LicenseHolderUCIDatabase/(?P<licenseHolderId>\d+)/$', views.LicenseHolderUCIDatabase),
	re_path(r'^.*LicenseHolderUCIDatabaseUpdate/(?P<licenseHolderId>\d+)/(?P<iUciRecord>\d+)/$', views.LicenseHolderUCIDatabaseUpdate),
	re_path(r'^.*LicenseHolderUCIDatabaseUpdate/(?P<licenseHolderId>\d+)/(?P<iUciRecord>\d+)/(?P<confirmed>\d+)/$', views.LicenseHolderUCIDatabaseUpdate),
	re_path(r'^.*LicenseHolderDelete/(?P<licenseHolderId>\d+)/$', views.LicenseHolderDelete),
	re_path(r'^.*LicenseHolderTeamChange/(?P<licenseHolderId>\d+)/(?P<disciplineId>\d+)/$', views.LicenseHolderTeamChange),
	re_path(r'^.*LicenseHolderTeamSelect/(?P<licenseHolderId>\d+)/(?P<disciplineId>\d+)/(?P<teamId>\d+)/$', views.LicenseHolderTeamSelect),
	re_path(r'^.*LicenseHoldersImportExcel/$', views.LicenseHoldersImportExcel),
	re_path(r'^.*LicenseHoldersCorrectErrors/$', views.LicenseHoldersCorrectErrors),
	re_path(r'^.*LicenseHoldersAutoCreateTags/$', views.LicenseHoldersAutoCreateTags),
	re_path(r'^.*LicenseHoldersAutoCreateTags/(?P<confirmed>\d+)/$', views.LicenseHoldersAutoCreateTags),
	re_path(r'^.*LicenseHoldersManageDuplicates/$', views.LicenseHoldersManageDuplicates),
	re_path(r'^.*LicenseHoldersSelectDuplicates/(?P<duplicateIds>[0-9,]+)/$', views.LicenseHoldersSelectDuplicates),
	re_path(r'^.*LicenseHoldersSelectMergeDuplicate/(?P<duplicateIds>[0-9,]+)/$', views.LicenseHoldersSelectMergeDuplicate),
	re_path(r'^.*LicenseHoldersMergeDuplicates/(?P<mergeId>\d+)/(?P<duplicateIds>[0-9,]+)/$', views.LicenseHoldersMergeDuplicates),
	re_path(r'^.*LicenseHoldersMergeDuplicatesOK/(?P<mergeId>\d+)/(?P<duplicateIds>[0-9,]+)/$', views.LicenseHoldersMergeDuplicatesOK),
	re_path(r'^.*LicenseHoldersResetExistingBibs/$', views.LicenseHoldersResetExistingBibs),
	re_path(r'^.*LicenseHoldersResetExistingBibs/(?P<confirmed>\d+)/$', views.LicenseHoldersResetExistingBibs),
	re_path(r'^.*LicenseHoldersResetExistingTags/$', views.LicenseHoldersResetExistingTags),
	re_path(r'^.*LicenseHoldersResetExistingTags/(?P<confirmed>\d+)/$', views.LicenseHoldersResetExistingTags),
	re_path(r'^.*LicenseHoldersCloudImport/$', views.LicenseHoldersCloudImport),
	re_path(r'^.*LicenseHoldersCloudImport/(?P<confirmed>\d+)/$', views.LicenseHoldersCloudImport),
	
	re_path(r'^.*LicenseHolderCloudDownload/$', views.LicenseHolderCloudDownload),
	
	re_path(r'^.*CompetitionCloudQuery/$', views.CompetitionCloudQuery),
	re_path(r'^.*CompetitionCloudExport/(?P<competitionId>\d+)/$', views.CompetitionCloudExport),
	
	re_path(r'^.*CompetitionCloudImportList/$', views.CompetitionCloudImportList),
	
	re_path(r'^.*Teams/$', team.TeamsDisplay),
	re_path(r'^.*TeamNew/$', team.TeamNew),
	re_path(r'^.*TeamEdit/(?P<teamId>\d+)/$', team.TeamEdit),
	re_path(r'^.*TeamDelete/(?P<teamId>\d+)/$', team.TeamDelete),
	re_path(r'^.*TeamManageDuplicates/$', team.TeamManageDuplicates),
	re_path(r'^.*TeamManageDuplicatesSelect/$', team.TeamManageDuplicatesSelect),
	
	re_path(r'^.*TeamAliasNew/(?P<teamId>\d+)/$', team.TeamAliasNew),
	re_path(r'^.*TeamAliasEdit/(?P<teamAliasId>\d+)/$', team.TeamAliasEdit),
	re_path(r'^.*TeamAliasDelete/(?P<teamAliasId>\d+)/$', team.TeamAliasDelete),

	re_path(r'^.*LegalEntities/$', legal_entity.LegalEntitiesDisplay),
	re_path(r'^.*LegalEntityNew/$', legal_entity.LegalEntityNew),
	re_path(r'^.*LegalEntityEdit/(?P<legalEntityId>\d+)/$', legal_entity.LegalEntityEdit),
	re_path(r'^.*LegalEntityDelete/(?P<legalEntityId>\d+)/$', legal_entity.LegalEntityDelete),
	
	re_path(r'^.*CategoryFormats/$', category.CategoryFormatsDisplay),
	re_path(r'^.*CategoryFormatNew/$', category.CategoryFormatNew),
	re_path(r'^.*CategoryFormatEdit/(?P<categoryFormatId>\d+)/$', category.CategoryFormatEdit),
	re_path(r'^.*CategoryFormatCopy/(?P<categoryFormatId>\d+)/$', category.CategoryFormatCopy),
	re_path(r'^.*CategoryFormatDelete/(?P<categoryFormatId>\d+)/$', category.CategoryFormatDelete),
	
	re_path(r'^.*CategoryNew/(?P<categoryFormatId>\d+)/$', category.CategoryNew),
	re_path(r'^.*CategoryEdit/(?P<categoryId>\d+)/$', category.CategoryEdit),
	re_path(r'^.*CategoryDelete/(?P<categoryId>\d+)/$', category.CategoryDelete),
	
	re_path(r'^.*NumberSets/$', number_set.NumberSetsDisplay),
	re_path(r'^.*NumberSetNew/$', number_set.NumberSetNew),
	re_path(r'^.*NumberSetEdit/(?P<numberSetId>\d+)/$', number_set.NumberSetEdit),
	re_path(r'^.*NumberSetDelete/(?P<numberSetId>\d+)/$', number_set.NumberSetDelete),
	re_path(r'^.*NumberSetManage/(?P<numberSetId>\d+)/$', number_set.NumberSetManage),
	re_path(r'^.*NumberSetUp/(?P<numberSetId>\d+)/$', number_set.NumberSetUp),
	re_path(r'^.*NumberSetDown/(?P<numberSetId>\d+)/$', number_set.NumberSetDown),
	re_path(r'^.*NumberSetTop/(?P<numberSetId>\d+)/$', number_set.NumberSetTop),
	re_path(r'^.*NumberSetBottom/(?P<numberSetId>\d+)/$', number_set.NumberSetBottom),
	re_path(r'^.*BibReturn/(?P<numberSetEntryId>\d+)/$', number_set.BibReturn),
	re_path(r'^.*BibReturn/(?P<numberSetEntryId>\d+)/(?P<confirmed>\d+)/$', number_set.BibReturn),
	re_path(r'^.*BibLost/(?P<numberSetEntryId>\d+)/$', number_set.BibLost),
	re_path(r'^.*BibLost/(?P<numberSetEntryId>\d+)/(?P<confirmed>\d+)/$', number_set.BibLost),
	re_path(r'^.*NumberSetUploadExcel/(?P<numberSetId>\d+)/$', number_set.UploadNumberSet),
	re_path(r'^.*NumberSetBibList/(?P<numberSetId>\d+)/$', number_set.NumberSetBibList),
	
	re_path(r'^.*SeasonsPasses/$', seasons_pass.SeasonsPassesDisplay),
	re_path(r'^.*SeasonsPassNew/$', seasons_pass.SeasonsPassNew),
	re_path(r'^.*SeasonsPassCopy/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassCopy),
	re_path(r'^.*SeasonsPassEdit/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassEdit),
	re_path(r'^.*SeasonsPassDelete/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassDelete),
	re_path(r'^.*SeasonsPassUp/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassUp),
	re_path(r'^.*SeasonsPassDown/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassDown),
	re_path(r'^.*SeasonsPassTop/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassTop),
	re_path(r'^.*SeasonsPassBottom/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassBottom),
	
	re_path(r'^.*SeasonsPassHolderAdd/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassHolderAdd),
	re_path(r'^.*SeasonsPassHolderRemove/(?P<seasonsPassHolderId>\d+)/$', seasons_pass.SeasonsPassHolderRemove),
	re_path(r'^.*SeasonsPassLicenseHolderAdd/(?P<seasonsPassId>\d+)/(?P<licenseHolderId>\d+)/$', seasons_pass.SeasonsPassLicenseHolderAdd),
	re_path(r'^.*SeasonsPassLicenseHolderRemove/(?P<seasonsPassId>\d+)/(?P<licenseHolderId>\d+)/$', seasons_pass.SeasonsPassLicenseHolderRemove),
	re_path(r'^.*SeasonsPassHolderUploadExcel/(?P<seasonsPassId>\d+)/$', seasons_pass.UploadSeasonsPass),
	
	re_path(r'^.*RaceClasses/$', race_class.RaceClassesDisplay),
	re_path(r'^.*RaceClassNew/$', race_class.RaceClassNew),
	re_path(r'^.*RaceClassEdit/(?P<raceClassId>\d+)/$', race_class.RaceClassEdit),
	re_path(r'^.*RaceClassDelete/(?P<raceClassId>\d+)/$', race_class.RaceClassDelete),
	
	re_path(r'^.*Disciplines/$', discipline.DisciplinesDisplay),
	re_path(r'^.*DisciplineNew/$', discipline.DisciplineNew),
	re_path(r'^.*DisciplineEdit/(?P<disciplineId>\d+)/$', discipline.DisciplineEdit),
	re_path(r'^.*DisciplineDelete/(?P<disciplineId>\d+)/$', discipline.DisciplineDelete),
	re_path(r'^.*DisciplineUp/(?P<disciplineId>\d+)/$', discipline.DisciplineUp),
	re_path(r'^.*DisciplineDown/(?P<disciplineId>\d+)/$', discipline.DisciplineDown),
	re_path(r'^.*DisciplineTop/(?P<disciplineId>\d+)/$', discipline.DisciplineTop),
	re_path(r'^.*DisciplineBottom/(?P<disciplineId>\d+)/$', discipline.DisciplineBottom),
	
	re_path(r'^.*ReportLabels/$', report_label.ReportLabelsDisplay),
	re_path(r'^.*ReportLabelNew/$', report_label.ReportLabelNew),
	re_path(r'^.*ReportLabelEdit/(?P<reportLabelId>\d+)/$', report_label.ReportLabelEdit),
	re_path(r'^.*ReportLabelDelete/(?P<reportLabelId>\d+)/$', report_label.ReportLabelDelete),
	
	re_path(r'^.*GetEvents/$', views.GetEvents),
	re_path(r'^.*GetEvents/(?P<date>\d\d\d\d-\d\d-\d\d)/$', views.GetEvents),
	
	re_path(r'^.*SystemInfoEdit/$', views.SystemInfoEdit),
	re_path(r'^.*UpdateLogShow/$', views.UpdateLogShow),
	re_path(r'^.*DownloadDatabase/$', views.DownloadDatabase),
	re_path(r'^.*AttendanceAnalytics/$', views.AttendanceAnalytics),
	re_path(r'^.*ParticipantReport/$', views.ParticipantReport),
	re_path(r'^.*YearOnYearAnalytics/$', views.YearOnYearAnalytics),
	re_path(r'^.*QRCode/$', views.QRCode),
	
	re_path(r'^.*Series/$', series.SeriesList),
	
	re_path(r'^.*SeriesNew/$', series.SeriesNew),
	re_path(r'^.*SeriesNew/(?P<categoryFormatId>\d+)/$', series.SeriesNew),
	re_path(r'^.*SeriesCopy/(?P<seriesId>\d+)/$', series.SeriesCopy),
	re_path(r'^.*SeriesEdit/(?P<seriesId>\d+)/$', series.SeriesEdit),
	re_path(r'^.*SeriesDetailEdit/(?P<seriesId>\d+)/$', series.SeriesDetailEdit),
	re_path(r'^.*SeriesDelete/(?P<seriesId>\d+)/$', series.SeriesDelete),
	re_path(r'^.*SeriesDelete/(?P<seriesId>\d+)/(?P<confirmed>\d+)/$', series.SeriesDelete),
	
	re_path(r'^.*SeriesPointsStructureNew/(?P<seriesId>\d+)/$', series.SeriesPointsStructureNew),
	re_path(r'^.*SeriesPointsStructureEdit/(?P<seriesPointsStructureId>\d+)/$', series.SeriesPointsStructureEdit),
	
	re_path(r'^.*SeriesCategoriesChange/(?P<seriesId>\d+)/$', series.SeriesCategoriesChange),
	
	re_path(r'^.*SeriesPointsStructureDelete/(?P<seriesPointsStructureId>\d+)/$', series.SeriesPointsStructureDelete),
	re_path(r'^.*SeriesPointsStructureDelete/(?P<seriesPointsStructureId>\d+)/(?P<confirmed>\d+)/$', series.SeriesPointsStructureDelete),
	
	re_path(r'^.*SeriesUpgradeProgressionNew/(?P<seriesId>\d+)/$', series.SeriesUpgradeProgressionNew),
	re_path(r'^.*SeriesUpgradeProgressionDelete/(?P<seriesUpgradeProgressionId>\d+)/$', series.SeriesUpgradeProgressionDelete),
	re_path(r'^.*SeriesUpgradeProgressionDelete/(?P<seriesUpgradeProgressionId>\d+)/(?P<confirmed>\d+)/$', series.SeriesUpgradeProgressionDelete),
	re_path(r'^.*SeriesUpgradeProgressionEdit/(?P<seriesUpgradeProgressionId>\d+)/$', series.SeriesUpgradeProgressionEdit),
	
	re_path(r'^.*SeriesCompetitionAdd/(?P<seriesId>\d+)/$', series.SeriesCompetitionAdd),
	re_path(r'^.*SeriesCompetitionAdd/(?P<seriesId>\d+)/(?P<competitionId>\d+)/$', series.SeriesCompetitionAdd),
	
	re_path(r'^.*SeriesCompetitionRemoveAll/(?P<seriesId>\d+)/$', series.SeriesCompetitionRemoveAll),
	re_path(r'^.*SeriesCompetitionRemoveAll/(?P<seriesId>\d+)/(?P<confirmed>\d+)/$', series.SeriesCompetitionRemoveAll),
	
	re_path(r'^.*SeriesCompetitionRemove/(?P<seriesId>\d+)/(?P<competitionId>\d+)/$', series.SeriesCompetitionRemove),
	re_path(r'^.*SeriesCompetitionRemove/(?P<seriesId>\d+)/(?P<competitionId>\d+)/(?P<confirmed>\d+)/$', series.SeriesCompetitionRemove),
	re_path(r'^.*SeriesCompetitionEdit/(?P<seriesId>\d+)/(?P<competitionId>\d+)/$', series.SeriesCompetitionEdit),
	
	re_path(r'^.*SeriesCategoryGroupNew/(?P<seriesId>\d+)/$', series.SeriesCategoryGroupNew),	
	re_path(r'^.*SeriesCategoryGroupDelete/(?P<categoryGroupId>\d+)/$', series.SeriesCategoryGroupDelete),
	re_path(r'^.*SeriesCategoryGroupDelete/(?P<categoryGroupId>\d+)/(?P<confirmed>\d+)/$', series.SeriesCategoryGroupDelete),
	re_path(r'^.*SeriesCategoryGroupEdit/(?P<categoryGroupId>\d+)/$', series.SeriesCategoryGroupEdit),
	
	re_path(r'^.*CustomCategoryNew/(?P<eventId>\d+)/(?P<eventType>\d+)/$', custom_category.CustomCategoryNew),
	re_path(r'^.*CustomCategoryEdit/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<customCategoryId>\d+)/$',
		custom_category.CustomCategoryEdit),
	re_path(r'^.*CustomCategoryMassStartEdit/(?P<customCategoryId>\d+)/$',
		custom_category.CustomCategoryMassStartEdit),
	re_path(r'^.*CustomCategoryTTEdit/(?P<customCategoryId>\d+)/$',
		custom_category.CustomCategoryTTEdit),
	re_path(r'^.*CustomCategoryDelete/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<customCategoryId>\d+)/$',
		custom_category.CustomCategoryDelete),
	re_path(r'^.*CustomCategoryDelete/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<customCategoryId>\d+)/(?P<confirmed>\d+)/$',
		custom_category.CustomCategoryDelete),
		
	re_path(r'^.*Resequence_(?P<modelClassName>[^_]+)_Class/(?P<instanceId>\d+)/(?P<newSequence>\d+)/$', views.Resequence),
	
	re_path(r'^PastCompetition/$', views.PastCompetition),
	
	re_path(r'^.*CrossMgrPasswords/$', crossmgr_password.CrossMgrPasswordDisplay),
	re_path(r'^.*CrossMgrPasswordNew/$', crossmgr_password.CrossMgrPasswordNew),
	re_path(r'^.*CrossMgrPasswordEdit/(?P<crossMgrPasswordId>\d+)/$', crossmgr_password.CrossMgrPasswordEdit),
	re_path(r'^.*CrossMgrPasswordDelete/(?P<crossMgrPasswordId>\d+)/$', crossmgr_password.CrossMgrPasswordDelete),
	
	re_path(r'^.*CrossMgrLogs/$', crossmgr_password.CrossMgrLogDisplay),
	re_path(r'^.*CrossMgrLogClear/$', crossmgr_password.CrossMgrLogClear),

	re_path(r'^.*Images/$', image.Images),
	re_path(r'^.*ImageNew/$', image.ImageNew),
	re_path(r'^.*ImageEdit/(?P<imageId>\d+)/$', image.ImageEdit),
	re_path(r'^.*ImageDelete/(?P<imageId>\d+)/$', image.ImageDelete),
	re_path(r'^.*ImageDelete/(?P<imageId>\d+)/(?P<confirmed>\d+)/$', image.ImageDelete),
	
	re_path(r'^.*GPXCourses/$', gpx_course.GPXCourses),
	re_path(r'^.*GPXCourseNew/$', gpx_course.GPXCourseNew),
	re_path(r'^.*GPXCourseEdit/(?P<gpxCourseId>\d+)/$', gpx_course.GPXCourseEdit),
	re_path(r'^.*GPXCourseDelete/(?P<gpxCourseId>\d+)/$', gpx_course.GPXCourseDelete),
	re_path(r'^.*GPXCourseDelete/(?P<gpxCourseId>\d+)/(?P<confirmed>\d+)/$', gpx_course.GPXCourseDelete),
	
	re_path(r'^[Ll]ogin/$',  auth_views.LoginView.as_view(template_name='login.html'), name='login'),
	re_path(r'^.*[Ll]ogout/$', views.Logout),
]
