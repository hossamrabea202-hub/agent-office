# i5 helper: join a Multi-User session by name without restarting (only works while disconnected).
#   py ".../mu_join_ue.py" <SessionName>
import sys, unreal
M = unreal.MultiUserClientStatics
c = unreal.MultiUserClientConfig()
c.set_editor_property('default_server_url', 'CastleDefenderServer'); c.set_editor_property('default_session_name', sys.argv[1])
print('status before', M.get_multi_user_connection_status_detail())
print('configure', M.configure_multi_user_client(c), 'start', M.start_multi_user_default_connection())
