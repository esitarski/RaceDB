from django.conf.urls import url
from django.contrib.auth.views import login
from django.views.generic import RedirectView

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
from core import results
from core import hub
from core import series
from core import callups
from core import custom_label

import warnings
warnings.simplefilter('error', DeprecationWarning)

urlpatterns = [
	url(r'^$', views.home, name='home'),
	url(r'^(?P<rfid_antenna>\d+)/$', views.home),
	url(r'^(?i)Home/$', views.home),
	
	url(r'^(?i).*Hub/$', RedirectView.as_view(url='/RaceDB/Hub/SearchCompetitions/')),
	url(r'^(?i).*Hub/SearchCompetitions/$', hub.SearchCompetitions),
	url(r'^(?i).*Hub/CompetitionResults/(?P<competitionId>\d+)/$', hub.CompetitionResults),
	url(r'^(?i).*Hub/CategoryResults/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<categoryId>\d+)/$', hub.CategoryResults),
	
	url(r'^(?i).*Hub/LicenseHolderResults/(?P<licenseHolderId>\d+)/$', hub.LicenseHolderResults),
	url(r'^(?i).*Hub/ResultAnalysis/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<resultId>\d+)/$', hub.ResultAnalysis),
	
	url(r'^(?i).*Hub/SearchLicenseHolders/$', hub.SearchLicenseHolders),
	
	url(r'^(?i).*Hub/Series/$', hub.SeriesList),
	url(r'^(?i).*Hub/SeriesCategories/(?P<seriesId>\d+)/$', hub.SeriesCategories),
	url(r'^(?i).*Hub/SeriesCategoryResults/(?P<seriesId>\d+)/(?P<categoryId>\d+)/$', hub.SeriesCategoryResults),
	
	url(r'^(?i).*SelfServe/$', self_serve.SelfServe),
	url(r'^(?i).*SelfServe/(?P<do_scan>\d+)/$', self_serve.SelfServe),
	url(r'^(?i).*SelfServe/SelfServeQR/$', self_serve.SelfServeQRCode),
	
	url(r'^(?i).*Competitions/$', views.CompetitionsDisplay),
	url(r'^(?i).*CompetitionNew/$', views.CompetitionNew),
	url(r'^(?i).*CompetitionCopy/(?P<competitionId>\d+)/$', views.CompetitionCopy),
	url(r'^(?i).*CompetitionEdit/(?P<competitionId>\d+)/$', views.CompetitionEdit),
	url(r'^(?i).*CompetitionExport/(?P<competitionId>\d+)/$', views.CompetitionExport),
	url(r'^(?i).*CompetitionImport/$', views.CompetitionImport),
	url(r'^(?i).*CompetitionDelete/(?P<competitionId>\d+)/$', views.CompetitionDelete),
	url(r'^(?i).*CompetitionDashboard/(?P<competitionId>\d+)/$', views.CompetitionDashboard),
	url(r'^(?i).*CompetitionRegAnalytics/(?P<competitionId>\d+)/$', views.CompetitionRegAnalytics),
	url(r'^(?i).*CompetitionApplyOptionalEventChangesToExistingParticipants/(?P<competitionId>\d+)/$', views.CompetitionApplyOptionalEventChangesToExistingParticipants),
	url(r'^(?i).*CompetitionApplyOptionalEventChangesToExistingParticipants/(?P<competitionId>\d+)/(?P<confirmed>\d+)/$', views.CompetitionApplyOptionalEventChangesToExistingParticipants),
	url(r'^(?i).*TeamsShow/(?P<competitionId>\d+)/$', views.TeamsShow),
	url(r'^(?i).*UploadPrereg/(?P<competitionId>\d+)/$', views.UploadPrereg),
	url(r'^(?i).*FinishLynx/(?P<competitionId>\d+)/$', views.FinishLynx),
	url(r'^(?i).*StartLists/(?P<competitionId>\d+)/$', views.StartLists),
	url(r'^(?i).*StartList/(?P<eventId>\d+)/$', views.StartList),
	
	url(r'^(?i).*CompetitionCloudUpload/$', views.CompetitionCloudUpload),
	
	url(r'^(?i).*ApplyNumberSet/(?P<competitionId>\d+)/$', views.ApplyNumberSet),
	url(r'^(?i).*InitializeNumberSet/(?P<competitionId>\d+)/$', views.InitializeNumberSet),
	
	url(r'^(?i).*StartListTT/(?P<eventTTId>\d+)/$', views.StartListTT),
	
	url(r'^(?i).*StartListEmails/(?P<eventId>\d+)/(?P<eventType>\d+)/$', views.StartListEmails),
	url(r'^(?i).*StartListExcelDownload/(?P<eventId>\d+)/(?P<eventType>\d+)/$', views.StartListExcelDownload),
	
	url(r'^(?i).*UCIExcelDownload/(?P<eventId>\d+)/(?P<eventType>\d+)/$', views.UCIExcelDownload),
	url(r'^(?i).*UCIExcelDownload/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<startList>\d+)/$', views.UCIExcelDownload),
	
	url(r'^(?i).*ParticipantBarcodeAdd/(?P<competitionId>\d+)/$', participant.ParticipantBarcodeAdd),
	url(r'^(?i).*ParticipantRfidAdd/(?P<competitionId>\d+)/$', participant.ParticipantRfidAdd),
	url(r'^(?i).*ParticipantRfidAdd/(?P<competitionId>\d+)/(?P<autoSubmit>\d+)/$', participant.ParticipantRfidAdd),
	url(r'^(?i).*ParticipantBibAdd/(?P<competitionId>\d+)/$', participant.ParticipantBibAdd),
	
	url(r'^(?i).*CategoryNumbers/(?P<competitionId>\d+)/$', category_numbers.CategoryNumbersDisplay),
	url(r'^(?i).*CategoryNumbersNew/(?P<competitionId>\d+)/$', category_numbers.CategoryNumbersNew),
	url(r'^(?i).*CategoryNumbersEdit/(?P<categoryNumbersId>\d+)/$', category_numbers.CategoryNumbersEdit),
	url(r'^(?i).*CategoryNumbersDelete/(?P<categoryNumbersId>\d+)/$', category_numbers.CategoryNumbersDelete),
	
	url(r'^(?i).*EventMassStarts/(?P<competitionId>\d+)/$', views.EventMassStartDisplay),
	url(r'^(?i).*EventMassStartNew/(?P<competitionId>\d+)/$', views.EventMassStartNew),
	url(r'^(?i).*EventMassStartEdit/(?P<eventId>\d+)/$', views.EventMassStartEdit),
	url(r'^(?i).*EventMassStartCrossMgr/(?P<eventId>\d+)/$', views.EventMassStartCrossMgr),
	url(r'^(?i).*EventMassStartDelete/(?P<eventId>\d+)/$', views.EventMassStartDelete),
	
	url(r'^(?i).*UploadCrossMgr/$', views.UploadCrossMgr),
	
	url(r'^(?i).*CustomLabel/(?P<competitionId>\d+)/$', custom_label.CustomLabel),
	
	url(r'^(?i).*WaveNew/(?P<eventMassStartId>\d+)/$', views.WaveNew),
	url(r'^(?i).*WaveEdit/(?P<waveId>\d+)/$', views.WaveEdit),
	url(r'^(?i).*WaveDelete/(?P<waveId>\d+)/$', views.WaveDelete),
	
	url(r'^(?i).*EventTTs/(?P<competitionId>\d+)/$', views.EventTTDisplay),
	url(r'^(?i).*EventTTNew/(?P<competitionId>\d+)/$', views.EventTTNew),
	url(r'^(?i).*EventTTEdit/(?P<eventTTId>\d+)/$', views.EventTTEdit),
	url(r'^(?i).*EventTTCrossMgr/(?P<eventTTId>\d+)/$', views.EventTTCrossMgr),
	url(r'^(?i).*EventTTDelete/(?P<eventTTId>\d+)/$', views.EventTTDelete),
	
	url(r'^(?i).*EventApplyToExistingParticipants/(?P<eventId>\d+)/$', views.EventApplyToExistingParticipants),
	url(r'^(?i).*EventApplyToExistingParticipants/(?P<eventId>\d+)/(?P<confirmed>\d+)/$', views.EventApplyToExistingParticipants),
	
	url(r'^(?i).*SeedingEdit/(?P<eventTTId>\d+)/$', views.SeedingEdit),
	url(r'^(?i).*GenerateStartTimes/(?P<eventTTId>\d+)/$', views.GenerateStartTimes),
	
	url(r'^(?i).*WaveTTNew/(?P<eventTTId>\d+)/$', views.WaveTTNew),
	url(r'^(?i).*WaveTTEdit/(?P<waveTTId>\d+)/$', views.WaveTTEdit),
	url(r'^(?i).*WaveTTDelete/(?P<waveTTId>\d+)/$', views.WaveTTDelete),
	url(r'^(?i).*WaveTTUp/(?P<waveTTId>\d+)/$', views.WaveTTUp),
	url(r'^(?i).*WaveTTDown/(?P<waveTTId>\d+)/$', views.WaveTTDown),
	
	url(r'^(?i).*Callups/(?P<eventId>\d+)/(?P<eventType>\d+)/(?P<seriesId>\d+)/$', callups.Callups),
	
	url(r'^(?i).*Participants/(?P<competitionId>\d+)/$', participant.Participants),
	url(r'^(?i).*ParticipantsInEvents/(?P<competitionId>\d+)/$', participant.ParticipantsInEvents),
	url(r'^(?i).*ParticipantManualAdd/(?P<competitionId>\d+)/$', participant.ParticipantManualAdd),
	url(r'^(?i).*ParticipantAddToCompetition/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', participant.ParticipantAddToCompetition),
	url(r'^(?i).*ParticipantAddToCompetitionDifferentCategory/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$',
				participant.ParticipantAddToCompetitionDifferentCategory),
	url(r'^(?i).*ParticipantAddToCompetitionDifferentCategoryConfirm/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$',
				participant.ParticipantAddToCompetitionDifferentCategoryConfirm),
	url(r'^(?i).*ParticipantEdit/(?P<participantId>\d+)/$', participant.ParticipantEdit),
	url(r'^(?i).*ParticipantEditFromLicenseHolder/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', participant.ParticipantEditFromLicenseHolder),
	url(r'^(?i).*ParticipantRemove/(?P<participantId>\d+)/$', participant.ParticipantRemove),
	url(r'^(?i).*ParticipantDoDelete/(?P<participantId>\d+)/$', participant.ParticipantDoDelete),
	url(r'^(?i).*LicenseHolderAddConfirm/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', views.LicenseHolderAddConfirm),
	url(r'^(?i).*LicenseHolderConfirmAddToCompetition/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', views.LicenseHolderConfirmAddToCompetition),
	
	url(r'^(?i).*ParticipantCategoryChange/(?P<participantId>\d+)/$', participant.ParticipantCategoryChange ),
	url(r'^(?i).*ParticipantCategorySelect/(?P<participantId>\d+)/(?P<categoryId>\d+)/$', participant.ParticipantCategorySelect ),
	
	url(r'^(?i).*ParticipantRoleChange/(?P<participantId>\d+)/$', participant.ParticipantRoleChange ),
	url(r'^(?i).*ParticipantRoleSelect/(?P<participantId>\d+)/(?P<role>\d+)/$', participant.ParticipantRoleSelect ),
	
	url(r'^(?i).*ParticipantConfirmedChange/(?P<participantId>\d+)/$', participant.ParticipantBooleanChange, {'field':'confirmed'}),
	url(r'^(?i).*ParticipantPreregisteredChange/(?P<participantId>\d+)/$', participant.ParticipantBooleanChange, {'field':'preregistered'}),
	url(r'^(?i).*ParticipantPaidChange/(?P<participantId>\d+)/$', participant.ParticipantBooleanChange, {'field':'paid'}),
	
	url(r'^(?i).*ParticipantSignatureChange/(?P<participantId>\d+)/$', participant.ParticipantSignatureChange ),
	url(r'^(?i).*SetSignatureWithTouchScreen/(?P<use_touch_screen>\d+)/$', participant.SetSignatureWithTouchScreen ),
	
	url(r'^(?i).*ParticipantTeamChange/(?P<participantId>\d+)/$', participant.ParticipantTeamChange ),
	url(r'^(?i).*ParticipantTeamSelect/(?P<participantId>\d+)/(?P<teamId>\d+)/$', participant.ParticipantTeamSelect ),
	
	url(r'^(?i).*ParticipantBibChange/(?P<participantId>\d+)/$', participant.ParticipantBibChange ),
	url(r'^(?i).*ParticipantBibSelect/(?P<participantId>\d+)/(?P<bib>\d+)/$', participant.ParticipantBibSelect ),
	
	url(r'^(?i).*ParticipantTagChange/(?P<participantId>\d+)/$', participant.ParticipantTagChange ),
	url(r'^(?i).*ParticipantNoteChange/(?P<participantId>\d+)/$', participant.ParticipantNoteChange ),
	url(r'^(?i).*ParticipantGeneralNoteChange/(?P<participantId>\d+)/$', participant.ParticipantGeneralNoteChange ),
	url(r'^(?i).*ParticipantOptionChange/(?P<participantId>\d+)/$', participant.ParticipantOptionChange ),
	url(r'^(?i).*ParticipantEstSpeedChange/(?P<participantId>\d+)/$', participant.ParticipantEstSpeedChange ),
	url(r'^(?i).*ParticipantWaiverChange/(?P<participantId>\d+)/$', participant.ParticipantWaiverChange ),
	url(r'^(?i).*ParticipantPrintBibLabels/(?P<participantId>\d+)/$', participant.ParticipantPrintBibLabels ),
	url(r'^(?i).*ParticipantPrintBodyBib/(?P<participantId>\d+)/$', participant.ParticipantPrintBodyBib ),
	url(r'^(?i).*ParticipantPrintBodyBib/(?P<participantId>\d+)/(?P<copies>\d+)/$', participant.ParticipantPrintBodyBib ),
	url(r'^(?i).*ParticipantPrintBodyBib/(?P<participantId>\d+)/(?P<copies>\d+)/(?P<onePage>\d+)/$', participant.ParticipantPrintBodyBib ),
	url(r'^(?i).*ParticipantPrintShoulderBib/(?P<participantId>\d+)/$', participant.ParticipantPrintShoulderBib ),
	url(r'^(?i).*ParticipantEmergencyContactInfo/(?P<participantId>\d+)/$', participant.ParticipantEmergencyContactInfo ),
	url(r'^(?i).*ParticipantPrintEmergencyContactInfo/(?P<participantId>\d+)/$', participant.ParticipantPrintEmergencyContactInfo ),
	
	url(r'^(?i).*LicenseHolders/$', views.LicenseHoldersDisplay),
	url(r'^(?i).*LicenseHolderNew/$', views.LicenseHolderNew),
	url(r'^(?i).*LicenseHolderBarcodeScan/$', views.LicenseHolderBarcodeScan),
	url(r'^(?i).*LicenseHolderRfidScan/$', views.LicenseHolderRfidScan),
	url(r'^(?i).*LicenseHolderTagChange/(?P<licenseHolderId>\d+)/$', views.LicenseHolderTagChange),
	url(r'^(?i).*LicenseHolderEdit/(?P<licenseHolderId>\d+)/$', views.LicenseHolderEdit),
	url(r'^(?i).*LicenseHolderDelete/(?P<licenseHolderId>\d+)/$', views.LicenseHolderDelete),
	url(r'^(?i).*LicenseHoldersImportExcel/$', views.LicenseHoldersImportExcel),
	url(r'^(?i).*LicenseHoldersCorrectErrors/$', views.LicenseHoldersCorrectErrors),
	url(r'^(?i).*LicenseHoldersAutoCreateTags/$', views.LicenseHoldersAutoCreateTags),
	url(r'^(?i).*LicenseHoldersAutoCreateTags/(?P<confirmed>\d+)/$', views.LicenseHoldersAutoCreateTags),
	url(r'^(?i).*LicenseHoldersManageDuplicates/$', views.LicenseHoldersManageDuplicates),
	url(r'^(?i).*LicenseHoldersSelectDuplicates/(?P<duplicateIds>[0123456789,]+)/$', views.LicenseHoldersSelectDuplicates),
	url(r'^(?i).*LicenseHoldersSelectMergeDuplicate/(?P<duplicateIds>[0123456789,]+)/$', views.LicenseHoldersSelectMergeDuplicate),
	url(r'^(?i).*LicenseHoldersMergeDuplicates/(?P<mergeId>\d+)/(?P<duplicateIds>[0123456789,]+)/$', views.LicenseHoldersMergeDuplicates),
	url(r'^(?i).*LicenseHoldersMergeDuplicatesOK/(?P<mergeId>\d+)/(?P<duplicateIds>[0123456789,]+)/$', views.LicenseHoldersMergeDuplicatesOK),
	url(r'^(?i).*LicenseHoldersResetExistingBibs/$', views.LicenseHoldersResetExistingBibs),
	url(r'^(?i).*LicenseHoldersResetExistingBibs/(?P<confirmed>\d+)/$', views.LicenseHoldersResetExistingBibs),
	url(r'^(?i).*LicenseHoldersCloudImport/$', views.LicenseHoldersCloudImport),
	url(r'^(?i).*LicenseHoldersCloudImport/(?P<confirmed>\d+)/$', views.LicenseHoldersCloudImport),
	
	url(r'^(?i).*LicenseHolderCloudDownload/$', views.LicenseHolderCloudDownload),
	
	url(r'^(?i).*CompetitionCloudQuery/$', views.CompetitionCloudQuery),
	url(r'^(?i).*CompetitionCloudExport/(?P<competitionId>\d+)/$', views.CompetitionCloudExport),
	
	url(r'^(?i).*CompetitionCloudImportList/$', views.CompetitionCloudImportList),
	
	url(r'^(?i).*Teams/$', team.TeamsDisplay),
	url(r'^(?i).*TeamNew/$', team.TeamNew),
	url(r'^(?i).*TeamEdit/(?P<teamId>\d+)/$', team.TeamEdit),
	url(r'^(?i).*TeamDelete/(?P<teamId>\d+)/$', team.TeamDelete),
	url(r'^(?i).*TeamManageDuplicates/$', team.TeamManageDuplicates),
	url(r'^(?i).*TeamManageDuplicatesSelect/$', team.TeamManageDuplicatesSelect),
	
	url(r'^(?i).*LegalEntities/$', legal_entity.LegalEntitiesDisplay),
	url(r'^(?i).*LegalEntityNew/$', legal_entity.LegalEntityNew),
	url(r'^(?i).*LegalEntityEdit/(?P<legalEntityId>\d+)/$', legal_entity.LegalEntityEdit),
	url(r'^(?i).*LegalEntityDelete/(?P<legalEntityId>\d+)/$', legal_entity.LegalEntityDelete),
	
	url(r'^(?i).*CategoryFormats/$', category.CategoryFormatsDisplay),
	url(r'^(?i).*CategoryFormatNew/$', category.CategoryFormatNew),
	url(r'^(?i).*CategoryFormatEdit/(?P<categoryFormatId>\d+)/$', category.CategoryFormatEdit),
	url(r'^(?i).*CategoryFormatCopy/(?P<categoryFormatId>\d+)/$', category.CategoryFormatCopy),
	url(r'^(?i).*CategoryFormatDelete/(?P<categoryFormatId>\d+)/$', category.CategoryFormatDelete),
	
	url(r'^(?i).*CategoryUp/(?P<categoryId>\d+)/$', category.CategoryUp),
	url(r'^(?i).*CategoryDown/(?P<categoryId>\d+)/$', category.CategoryDown),
	
	url(r'^(?i).*CategoryNew/(?P<categoryFormatId>\d+)/$', category.CategoryNew),
	url(r'^(?i).*CategoryEdit/(?P<categoryId>\d+)/$', category.CategoryEdit),
	url(r'^(?i).*CategoryDelete/(?P<categoryId>\d+)/$', category.CategoryDelete),
	
	url(r'^(?i).*NumberSets/$', number_set.NumberSetsDisplay),
	url(r'^(?i).*NumberSetNew/$', number_set.NumberSetNew),
	url(r'^(?i).*NumberSetEdit/(?P<numberSetId>\d+)/$', number_set.NumberSetEdit),
	url(r'^(?i).*NumberSetDelete/(?P<numberSetId>\d+)/$', number_set.NumberSetDelete),
	url(r'^(?i).*NumberSetManage/(?P<numberSetId>\d+)/$', number_set.NumberSetManage),
	url(r'^(?i).*NumberSetUp/(?P<numberSetId>\d+)/$', number_set.NumberSetUp),
	url(r'^(?i).*NumberSetDown/(?P<numberSetId>\d+)/$', number_set.NumberSetDown),
	url(r'^(?i).*NumberSetTop/(?P<numberSetId>\d+)/$', number_set.NumberSetTop),
	url(r'^(?i).*NumberSetBottom/(?P<numberSetId>\d+)/$', number_set.NumberSetBottom),
	url(r'^(?i).*BibReturn/(?P<numberSetEntryId>\d+)/$', number_set.BibReturn),
	url(r'^(?i).*BibReturn/(?P<numberSetEntryId>\d+)/(?P<confirmed>\d+)/$', number_set.BibReturn),
	url(r'^(?i).*BibLost/(?P<numberSetEntryId>\d+)/$', number_set.BibLost),
	url(r'^(?i).*BibLost/(?P<numberSetEntryId>\d+)/(?P<confirmed>\d+)/$', number_set.BibLost),
	url(r'^(?i).*NumberSetUploadExcel/(?P<numberSetId>\d+)/$', number_set.UploadNumberSet),
	url(r'^(?i).*NumberSetBibList/(?P<numberSetId>\d+)/$', number_set.NumberSetBibList),
	
	url(r'^(?i).*SeasonsPasses/$', seasons_pass.SeasonsPassesDisplay),
	url(r'^(?i).*SeasonsPassNew/$', seasons_pass.SeasonsPassNew),
	url(r'^(?i).*SeasonsPassCopy/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassCopy),
	url(r'^(?i).*SeasonsPassEdit/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassEdit),
	url(r'^(?i).*SeasonsPassDelete/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassDelete),
	url(r'^(?i).*SeasonsPassUp/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassUp),
	url(r'^(?i).*SeasonsPassDown/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassDown),
	url(r'^(?i).*SeasonsPassTop/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassTop),
	url(r'^(?i).*SeasonsPassBottom/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassBottom),
	
	url(r'^(?i).*SeasonsPassHolderAdd/(?P<seasonsPassId>\d+)/$', seasons_pass.SeasonsPassHolderAdd),
	url(r'^(?i).*SeasonsPassHolderRemove/(?P<seasonsPassHolderId>\d+)/$', seasons_pass.SeasonsPassHolderRemove),
	url(r'^(?i).*SeasonsPassLicenseHolderAdd/(?P<seasonsPassId>\d+)/(?P<licenseHolderId>\d+)/$', seasons_pass.SeasonsPassLicenseHolderAdd),
	url(r'^(?i).*SeasonsPassLicenseHolderRemove/(?P<seasonsPassId>\d+)/(?P<licenseHolderId>\d+)/$', seasons_pass.SeasonsPassLicenseHolderRemove),
	url(r'^(?i).*SeasonsPassHolderUploadExcel/(?P<seasonsPassId>\d+)/$', seasons_pass.UploadSeasonsPass),
	
	url(r'^(?i).*RaceClasses/$', race_class.RaceClassesDisplay),
	url(r'^(?i).*RaceClassNew/$', race_class.RaceClassNew),
	url(r'^(?i).*RaceClassEdit/(?P<raceClassId>\d+)/$', race_class.RaceClassEdit),
	url(r'^(?i).*RaceClassDelete/(?P<raceClassId>\d+)/$', race_class.RaceClassDelete),
	url(r'^(?i).*RaceClassUp/(?P<raceClassId>\d+)/$', race_class.RaceClassUp),
	url(r'^(?i).*RaceClassDown/(?P<raceClassId>\d+)/$', race_class.RaceClassDown),
	url(r'^(?i).*RaceClassTop/(?P<raceClassId>\d+)/$', race_class.RaceClassTop),
	url(r'^(?i).*RaceClassBottom/(?P<raceClassId>\d+)/$', race_class.RaceClassBottom),
	
	url(r'^(?i).*Disciplines/$', discipline.DisciplinesDisplay),
	url(r'^(?i).*DisciplineNew/$', discipline.DisciplineNew),
	url(r'^(?i).*DisciplineEdit/(?P<disciplineId>\d+)/$', discipline.DisciplineEdit),
	url(r'^(?i).*DisciplineDelete/(?P<disciplineId>\d+)/$', discipline.DisciplineDelete),
	url(r'^(?i).*DisciplineUp/(?P<disciplineId>\d+)/$', discipline.DisciplineUp),
	url(r'^(?i).*DisciplineDown/(?P<disciplineId>\d+)/$', discipline.DisciplineDown),
	url(r'^(?i).*DisciplineTop/(?P<disciplineId>\d+)/$', discipline.DisciplineTop),
	url(r'^(?i).*DisciplineBottom/(?P<disciplineId>\d+)/$', discipline.DisciplineBottom),
	
	url(r'^(?i).*ReportLabels/$', report_label.ReportLabelsDisplay),
	url(r'^(?i).*ReportLabelNew/$', report_label.ReportLabelNew),
	url(r'^(?i).*ReportLabelEdit/(?P<reportLabelId>\d+)/$', report_label.ReportLabelEdit),
	url(r'^(?i).*ReportLabelDelete/(?P<reportLabelId>\d+)/$', report_label.ReportLabelDelete),
	url(r'^(?i).*ReportLabelUp/(?P<reportLabelId>\d+)/$', report_label.ReportLabelUp),
	url(r'^(?i).*ReportLabelDown/(?P<reportLabelId>\d+)/$', report_label.ReportLabelDown),
	url(r'^(?i).*ReportLabelTop/(?P<reportLabelId>\d+)/$', report_label.ReportLabelTop),
	url(r'^(?i).*ReportLabelBottom/(?P<reportLabelId>\d+)/$', report_label.ReportLabelBottom),
	
	url(r'^(?i).*GetEvents/$', views.GetEvents),
	url(r'^(?i).*GetEvents/(?P<date>\d\d\d\d-\d\d-\d\d)/$', views.GetEvents),
	
	url(r'^(?i).*SystemInfoEdit/$', views.SystemInfoEdit),
	url(r'^(?i).*UpdateLogShow/$', views.UpdateLogShow),
	url(r'^(?i).*AttendanceAnalytics/$', views.AttendanceAnalytics),
	url(r'^(?i).*ParticipantReport/$', views.ParticipantReport),
	url(r'^(?i).*YearOnYearAnalytics/$', views.YearOnYearAnalytics),
	url(r'^(?i).*QRCode/$', views.QRCode),
	
	url(r'^(?i).*Series/$', series.SeriesList),
	url(r'^(?i).*Series/(?P<moveDirection>\d+)/(?P<seriesId>\d+)/$', series.SeriesList),
	
	url(r'^(?i).*SeriesNew/$', series.SeriesNew),
	url(r'^(?i).*SeriesNew/(?P<categoryFormatId>\d+)/$', series.SeriesNew),
	url(r'^(?i).*SeriesCopy/(?P<seriesId>\d+)/$', series.SeriesCopy),
	url(r'^(?i).*SeriesEdit/(?P<seriesId>\d+)/$', series.SeriesEdit),
	url(r'^(?i).*SeriesDetailEdit/(?P<seriesId>\d+)/$', series.SeriesDetailEdit),
	url(r'^(?i).*SeriesDelete/(?P<seriesId>\d+)/$', series.SeriesDelete),
	url(r'^(?i).*SeriesDelete/(?P<seriesId>\d+)/(?P<confirmed>\d+)/$', series.SeriesDelete),
	
	url(r'^(?i).*SeriesPointsStructureNew/(?P<seriesId>\d+)/$', series.SeriesPointsStructureNew),
	url(r'^(?i).*SeriesPointsStructureEdit/(?P<seriesPointsStructureId>\d+)/$', series.SeriesPointsStructureEdit),
	
	url(r'^(?i).*SeriesCategoriesChange/(?P<seriesId>\d+)/$', series.SeriesCategoriesChange),
	
	url(r'^(?i).*SeriesPointsStructureDelete/(?P<seriesPointsStructureId>\d+)/$', series.SeriesPointsStructureDelete),
	url(r'^(?i).*SeriesPointsStructureDelete/(?P<seriesPointsStructureId>\d+)/(?P<confirmed>\d+)/$', series.SeriesPointsStructureDelete),
	
	url(r'^(?i).*SeriesPointsStructureMove/(?P<moveDirection>\d+)/(?P<seriesPointsStructureId>\d+)/$', series.SeriesPointsStructureMove),
	url(r'^(?i).*SeriesUpgradeProgressionMove/(?P<moveDirection>\d+)/(?P<seriesUpgradeProgressionId>\d+)/$', series.SeriesUpgradeProgressionMove),
	
	url(r'^(?i).*SeriesUpgradeProgressionNew/(?P<seriesId>\d+)/$', series.SeriesUpgradeProgressionNew),
	url(r'^(?i).*SeriesUpgradeProgressionDelete/(?P<seriesUpgradeProgressionId>\d+)/$', series.SeriesUpgradeProgressionDelete),
	url(r'^(?i).*SeriesUpgradeProgressionDelete/(?P<seriesUpgradeProgressionId>\d+)/(?P<confirmed>\d+)/$', series.SeriesUpgradeProgressionDelete),
	url(r'^(?i).*SeriesUpgradeProgressionEdit/(?P<seriesUpgradeProgressionId>\d+)/$', series.SeriesUpgradeProgressionEdit),
	
	url(r'^(?i).*SeriesCompetitionAdd/(?P<seriesId>\d+)/$', series.SeriesCompetitionAdd),
	url(r'^(?i).*SeriesCompetitionAdd/(?P<seriesId>\d+)/(?P<competitionId>\d+)/$', series.SeriesCompetitionAdd),
	
	url(r'^(?i).*SeriesCompetitionRemoveAll/(?P<seriesId>\d+)/$', series.SeriesCompetitionRemoveAll),
	url(r'^(?i).*SeriesCompetitionRemoveAll/(?P<seriesId>\d+)/(?P<confirmed>\d+)/$', series.SeriesCompetitionRemoveAll),
	
	url(r'^(?i).*SeriesCompetitionRemove/(?P<seriesId>\d+)/(?P<competitionId>\d+)/$', series.SeriesCompetitionRemove),
	url(r'^(?i).*SeriesCompetitionRemove/(?P<seriesId>\d+)/(?P<competitionId>\d+)/(?P<confirmed>\d+)/$', series.SeriesCompetitionRemove),
	url(r'^(?i).*SeriesCompetitionEdit/(?P<seriesId>\d+)/(?P<competitionId>\d+)/$', series.SeriesCompetitionEdit),
	
	url(r'^(?i).*SeriesCategoryGroupNew/(?P<seriesId>\d+)/$', series.SeriesCategoryGroupNew),	
	url(r'^(?i).*SeriesCategoryGroupDelete/(?P<categoryGroupId>\d+)/$', series.SeriesCategoryGroupDelete),
	url(r'^(?i).*SeriesCategoryGroupDelete/(?P<categoryGroupId>\d+)/(?P<confirmed>\d+)/$', series.SeriesCategoryGroupDelete),
	url(r'^(?i).*SeriesCategoryGroupMove/(?P<moveDirection>\d+)/(?P<categoryGroupId>\d+)/$', series.SeriesCategoryGroupMove),
	url(r'^(?i).*SeriesCategoryGroupEdit/(?P<categoryGroupId>\d+)/$', series.SeriesCategoryGroupEdit),
	
	url(r'^(?i)login/$', login, {'template_name': 'login.html'}, name='login'),
	url(r'^(?i).*logout/$', views.Logout),
]
