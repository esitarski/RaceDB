from django.conf.urls import url
from django.contrib.auth.views import login

from core import views
from core import self_serve
from core import number_set
from core import seasons_pass
from core import discipline
from core import race_class
from core import report_label
from core import category

import warnings
warnings.simplefilter('error', DeprecationWarning)

urlpatterns = [
	url(r'^$', views.home, name='home'),
	url(r'^(?P<rfid_antenna>\d+)/$', views.home, name='home'),
	url(r'^(?i)Home/$', views.home),
	
	url(r'^(?i).*Competitions/$', views.CompetitionsDisplay),
	url(r'^(?i).*CompetitionNew/$', views.CompetitionNew),
	url(r'^(?i).*CompetitionCopy/(?P<competitionId>\d+)/$', views.CompetitionCopy),
	url(r'^(?i).*CompetitionEdit/(?P<competitionId>\d+)/$', views.CompetitionEdit),
	url(r'^(?i).*CompetitionDelete/(?P<competitionId>\d+)/$', views.CompetitionDelete),
	url(r'^(?i).*CompetitionDashboard/(?P<competitionId>\d+)/$', views.CompetitionDashboard),
	url(r'^(?i).*CompetitionRegAnalytics/(?P<competitionId>\d+)/$', views.CompetitionRegAnalytics),
	url(r'^(?i).*TeamsShow/(?P<competitionId>\d+)/$', views.TeamsShow),
	url(r'^(?i).*UploadPrereg/(?P<competitionId>\d+)/$', views.UploadPrereg),
	url(r'^(?i).*FinishLynx/(?P<competitionId>\d+)/$', views.FinishLynx),
	url(r'^(?i).*StartLists/(?P<competitionId>\d+)/$', views.StartLists),
	url(r'^(?i).*StartList/(?P<eventId>\d+)/$', views.StartList),
	
	url(r'^(?i).*ApplyNumberSet/(?P<competitionId>\d+)/$', views.ApplyNumberSet),
	url(r'^(?i).*InitializeNumberSet/(?P<competitionId>\d+)/$', views.InitializeNumberSet),
	
	url(r'^(?i).*StartListTT/(?P<eventTTId>\d+)/$', views.StartListTT),
	
	url(r'^(?i).*StartListExcelDownload/(?P<eventId>\d+)/(?P<eventType>\d+)/$', views.StartListExcelDownload),
	
	url(r'^(?i).*ParticipantBarcodeAdd/(?P<competitionId>\d+)/$', views.ParticipantBarcodeAdd),
	url(r'^(?i).*ParticipantRfidAdd/(?P<competitionId>\d+)/$', views.ParticipantRfidAdd),
	url(r'^(?i).*ParticipantRfidAdd/(?P<competitionId>\d+)/(?P<autoSubmit>\d+)/$', views.ParticipantRfidAdd),
	
	url(r'^(?i).*CategoryNumbers/(?P<competitionId>\d+)/$', views.CategoryNumbersDisplay),
	url(r'^(?i).*CategoryNumbersNew/(?P<competitionId>\d+)/$', views.CategoryNumbersNew),
	url(r'^(?i).*CategoryNumbersEdit/(?P<categoryNumbersId>\d+)/$', views.CategoryNumbersEdit),
	url(r'^(?i).*CategoryNumbersDelete/(?P<categoryNumbersId>\d+)/$', views.CategoryNumbersDelete),
	
	url(r'^(?i).*EventMassStarts/(?P<competitionId>\d+)/$', views.EventMassStartDisplay),
	url(r'^(?i).*EventMassStartNew/(?P<competitionId>\d+)/$', views.EventMassStartNew),
	url(r'^(?i).*EventMassStartEdit/(?P<eventId>\d+)/$', views.EventMassStartEdit),
	url(r'^(?i).*EventMassStartCrossMgr/(?P<eventId>\d+)/$', views.EventMassStartCrossMgr),
	url(r'^(?i).*EventMassStartDelete/(?P<eventId>\d+)/$', views.EventMassStartDelete),
	
	url(r'^(?i).*WaveNew/(?P<eventMassStartId>\d+)/$', views.WaveNew),
	url(r'^(?i).*WaveEdit/(?P<waveId>\d+)/$', views.WaveEdit),
	url(r'^(?i).*WaveDelete/(?P<waveId>\d+)/$', views.WaveDelete),
	
	url(r'^(?i).*EventTTs/(?P<competitionId>\d+)/$', views.EventTTDisplay),
	url(r'^(?i).*EventTTNew/(?P<competitionId>\d+)/$', views.EventTTNew),
	url(r'^(?i).*EventTTEdit/(?P<eventTTId>\d+)/$', views.EventTTEdit),
	url(r'^(?i).*EventTTCrossMgr/(?P<eventTTId>\d+)/$', views.EventTTCrossMgr),
	url(r'^(?i).*EventTTDelete/(?P<eventTTId>\d+)/$', views.EventTTDelete),
	
	url(r'^(?i).*SeedingEdit/(?P<eventTTId>\d+)/$', views.SeedingEdit),
	url(r'^(?i).*GenerateStartTimes/(?P<eventTTId>\d+)/$', views.GenerateStartTimes),
	
	url(r'^(?i).*WaveTTNew/(?P<eventTTId>\d+)/$', views.WaveTTNew),
	url(r'^(?i).*WaveTTEdit/(?P<waveTTId>\d+)/$', views.WaveTTEdit),
	url(r'^(?i).*WaveTTDelete/(?P<waveTTId>\d+)/$', views.WaveTTDelete),
	url(r'^(?i).*WaveTTUp/(?P<waveTTId>\d+)/$', views.WaveTTUp),
	url(r'^(?i).*WaveTTDown/(?P<waveTTId>\d+)/$', views.WaveTTDown),
	
	url(r'^(?i).*Participants/(?P<competitionId>\d+)/$', views.Participants),
	url(r'^(?i).*ParticipantsInEvents/(?P<competitionId>\d+)/$', views.ParticipantsInEvents),
	url(r'^(?i).*ParticipantManualAdd/(?P<competitionId>\d+)/$', views.ParticipantManualAdd),
	url(r'^(?i).*ParticipantAddToCompetition/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', views.ParticipantAddToCompetition),
	url(r'^(?i).*ParticipantAddToCompetitionDifferentCategory/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$',
				views.ParticipantAddToCompetitionDifferentCategory),
	url(r'^(?i).*ParticipantAddToCompetitionDifferentCategoryConfirm/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$',
				views.ParticipantAddToCompetitionDifferentCategoryConfirm),
	url(r'^(?i).*ParticipantEdit/(?P<participantId>\d+)/$', views.ParticipantEdit),
	url(r'^(?i).*ParticipantEditFromLicenseHolder/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', views.ParticipantEditFromLicenseHolder),
	url(r'^(?i).*ParticipantRemove/(?P<participantId>\d+)/$', views.ParticipantRemove),
	url(r'^(?i).*ParticipantDoDelete/(?P<participantId>\d+)/$', views.ParticipantDoDelete),
	url(r'^(?i).*LicenseHolderAddConfirm/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', views.LicenseHolderAddConfirm),
	url(r'^(?i).*LicenseHolderConfirmAddToCompetition/(?P<competitionId>\d+)/(?P<licenseHolderId>\d+)/$', views.LicenseHolderConfirmAddToCompetition),
	
	url(r'^(?i).*ParticipantCategoryChange/(?P<participantId>\d+)/$', views.ParticipantCategoryChange ),
	url(r'^(?i).*ParticipantCategorySelect/(?P<participantId>\d+)/(?P<categoryId>\d+)/$', views.ParticipantCategorySelect ),
	
	url(r'^(?i).*ParticipantRoleChange/(?P<participantId>\d+)/$', views.ParticipantRoleChange ),
	url(r'^(?i).*ParticipantRoleSelect/(?P<participantId>\d+)/(?P<role>\d+)/$', views.ParticipantRoleSelect ),
	
	url(r'^(?i).*ParticipantConfirmedChange/(?P<participantId>\d+)/$', views.ParticipantBooleanChange, {'field':'confirmed'}),
	url(r'^(?i).*ParticipantPreregisteredChange/(?P<participantId>\d+)/$', views.ParticipantBooleanChange, {'field':'preregistered'}),
	url(r'^(?i).*ParticipantPaidChange/(?P<participantId>\d+)/$', views.ParticipantBooleanChange, {'field':'paid'}),
	
	url(r'^(?i).*ParticipantSignatureChange/(?P<participantId>\d+)/$', views.ParticipantSignatureChange ),
	url(r'^(?i).*SetSignatureWithTouchScreen/(?P<use_touch_screen>\d+)/$', views.SetSignatureWithTouchScreen ),
	
	url(r'^(?i).*ParticipantTeamChange/(?P<participantId>\d+)/$', views.ParticipantTeamChange ),
	url(r'^(?i).*ParticipantTeamSelect/(?P<participantId>\d+)/(?P<teamId>\d+)/$', views.ParticipantTeamSelect ),
	
	url(r'^(?i).*ParticipantBibChange/(?P<participantId>\d+)/$', views.ParticipantBibChange ),
	url(r'^(?i).*ParticipantBibSelect/(?P<participantId>\d+)/(?P<bib>\d+)/$', views.ParticipantBibSelect ),
	
	url(r'^(?i).*ParticipantTagChange/(?P<participantId>\d+)/$', views.ParticipantTagChange ),
	url(r'^(?i).*ParticipantNoteChange/(?P<participantId>\d+)/$', views.ParticipantNoteChange ),
	url(r'^(?i).*ParticipantGeneralNoteChange/(?P<participantId>\d+)/$', views.ParticipantGeneralNoteChange ),
	url(r'^(?i).*ParticipantOptionChange/(?P<participantId>\d+)/$', views.ParticipantOptionChange ),
	url(r'^(?i).*ParticipantEstSpeedChange/(?P<participantId>\d+)/$', views.ParticipantEstSpeedChange ),
	url(r'^(?i).*ParticipantWaiverChange/(?P<participantId>\d+)/$', views.ParticipantWaiverChange ),
	url(r'^(?i).*ParticipantPrintBibLabels/(?P<participantId>\d+)/$', views.ParticipantPrintBibLabels ),
	
	url(r'^(?i).*LicenseHolders/$', views.LicenseHoldersDisplay),
	url(r'^(?i).*LicenseHolderNew/$', views.LicenseHolderNew),
	url(r'^(?i).*LicenseHolderBarcodeScan/$', views.LicenseHolderBarcodeScan),
	url(r'^(?i).*LicenseHolderRfidScan/$', views.LicenseHolderRfidScan),
	url(r'^(?i).*LicenseHolderTagChange/(?P<licenseHolderId>\d+)/$', views.LicenseHolderTagChange),
	url(r'^(?i).*LicenseHolderEdit/(?P<licenseHolderId>\d+)/$', views.LicenseHolderEdit),
	url(r'^(?i).*LicenseHolderDelete/(?P<licenseHolderId>\d+)/$', views.LicenseHolderDelete),
	url(r'^(?i).*LicenseHoldersImportExcel/$', views.LicenseHoldersImportExcel),
	url(r'^(?i).*LicenseHoldersCorrectErrors/$', views.LicenseHoldersCorrectErrors),
	url(r'^(?i).*LicenseHoldersManageDuplicates/$', views.LicenseHoldersManageDuplicates),
	url(r'^(?i).*LicenseHoldersSelectDuplicates/(?P<duplicateIds>[0123456789,]+)/$', views.LicenseHoldersSelectDuplicates),
	url(r'^(?i).*LicenseHoldersSelectMergeDuplicate/(?P<duplicateIds>[0123456789,]+)/$', views.LicenseHoldersSelectMergeDuplicate),
	url(r'^(?i).*LicenseHoldersMergeDuplicates/(?P<mergeId>\d+)/(?P<duplicateIds>[0123456789,]+)/$', views.LicenseHoldersMergeDuplicates),
	url(r'^(?i).*LicenseHoldersMergeDuplicatesOK/(?P<mergeId>\d+)/(?P<duplicateIds>[0123456789,]+)/$', views.LicenseHoldersMergeDuplicatesOK),
	
	url(r'^(?i).*Teams/$', views.TeamsDisplay),
	url(r'^(?i).*TeamNew/$', views.TeamNew),
	url(r'^(?i).*TeamEdit/(?P<teamId>\d+)/$', views.TeamEdit),
	url(r'^(?i).*TeamDelete/(?P<teamId>\d+)/$', views.TeamDelete),
	
	url(r'^(?i).*LegalEntities/$', views.LegalEntitiesDisplay),
	url(r'^(?i).*LegalEntityNew/$', views.LegalEntityNew),
	url(r'^(?i).*LegalEntityEdit/(?P<legalEntityId>\d+)/$', views.LegalEntityEdit),
	url(r'^(?i).*LegalEntityDelete/(?P<legalEntityId>\d+)/$', views.LegalEntityDelete),
	
	url(r'^(?i).*CategoryFormats/$', category.CategoryFormatsDisplay),
	url(r'^(?i).*CategoryFormatNew/$', category.CategoryFormatNew),
	url(r'^(?i).*CategoryFormatEdit/(?P<categoryFormatId>\d+)/$', category.CategoryFormatEdit),
	url(r'^(?i).*CategoryFormatCopy/(?P<categoryFormatId>\d+)/$', category.CategoryFormatCopy),
	url(r'^(?i).*CategoryFormatDelete/(?P<categoryFormatId>\d+)/$', category.CategoryFormatDelete),
	
	url(r'^(?i).*CategoryUp/(?P<categoryId>\d+)/$', category.CategoryUp),
	url(r'^(?i).*CategoryDown/(?P<categoryId>\d+)/$', category.CategoryDown),
	
	url(r'^(?i).*CategoryNew/(?P<categoryFormatId>\d+)/$', category.CategoryNew, name='catetory_new'),
	url(r'^(?i).*CategoryEdit/(?P<categoryId>\d+)/$', category.CategoryEdit, name='category_edit'),
	url(r'^(?i).*CategoryDelete/(?P<categoryId>\d+)/$', category.CategoryDelete, name='category_delete'),
	
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
	url(r'^(?i).*AttendanceAnalytics/$', views.AttendanceAnalytics),
	url(r'^(?i).*ParticipantReport/$', views.ParticipantReport),
	url(r'^(?i).*YearOnYearAnalytics/$', views.YearOnYearAnalytics),
	url(r'^(?i).*QRCode/$', views.QRCode),
	
	url(r'^(?i).*SelfServe/$', self_serve.SelfServe),
	url(r'^(?i).*SelfServe/(?P<do_scan>\d+)/$', self_serve.SelfServe),
	url(r'^(?i).*SelfServe/SelfServeQR/$', self_serve.SelfServeQRCode),
	
	url(r'^(?i)login/$', login, {'template_name': 'login.html'}),
	url(r'^(?i).*logout/$', views.Logout),
]
