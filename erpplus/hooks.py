from . import __version__ as app_version

app_name = "erpplus"
app_title = "Erpplus"
app_publisher = "Kossivi"
app_description = "All customization"
app_email = "dodziamouzou@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/erpplus/css/erpplus.css"
# app_include_js = "/assets/erpplus/js/erpplus.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpplus/css/erpplus.css"
# web_include_js = "/assets/erpplus/js/erpplus.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpplus/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "erpplus.utils.jinja_methods",
#	"filters": "erpplus.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "erpplus.install.before_install"
# after_install = "erpplus.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "erpplus.uninstall.before_uninstall"
# after_uninstall = "erpplus.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpplus.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "Stock Entry": "erpplus.overrides.stock_entry.CustomStockEntry"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"erpplus.tasks.all"
#	],
#	"daily": [
#		"erpplus.tasks.daily"
#	],
#	"hourly": [
#		"erpplus.tasks.hourly"
#	],
#	"weekly": [
#		"erpplus.tasks.weekly"
#	],
#	"monthly": [
#		"erpplus.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "erpplus.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "erpplus.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "erpplus.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["erpplus.utils.before_request"]
# after_request = ["erpplus.utils.after_request"]

# Job Events
# ----------
# before_job = ["erpplus.utils.before_job"]
# after_job = ["erpplus.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"erpplus.auth.validate"
# ]

fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Erpplus"]]},
    {"dt": "Client Script", "filters": [["enabled", "=", 1],["module", "=", "Erpplus"]]},
    {"dt": "Server Script", "filters": [["disabled", "=", 0],["module", "=", "Erpplus"]]},
]