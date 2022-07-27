from ctm_python_client.core.workflow import Workflow, WorkflowDefaults
from ctm_python_client.core.comm import Environment
from aapi.job import *

folder = Folder('SampleFolder',
                controlm_server='ctmserver',
                site_standard='sitestd',
                business_fields=[{'Department': 'HR'}, {'Company': 'BMC'}],
                order_method=Folder.OrderMethod.Manual,
                application='ApplicationName',
                sub_application='SubApplication',
                run_as='controlm',
                when=Folder.When(week_days=['SUN']),
                active_retention_policy=Folder.ActiveRetentionPolicy.KeepAll,
                days_keep_active='41',
                confirm=True,
                created_by='user',
                description='FolderSample with lot of properties set',
                priority=Folder.Priority.High,
                rerun=Folder.Rerun(every='2'),
                rerun_limit=Folder.RerunLimit(times='3'),
                time_zone='HAW',
                variables=[{'var1': 'val'}, {'var2': 'val2'}],
                job_list=[]
                )

cpaws = ConnectionProfileAWS('AWS_CONNECTION_IAMROLE',
                             centralized=True,
                             iam_role='myrole',
                             region='ap-northeast-1',
                             proxy_settings=ConnectionProfileAWS.ProxySettings(
                                 host='host',
                                 port='12345',
                                 username='user',
                                 password='pass'
                             )
                             )
                             
job = JobEmbeddedScript('JobEmbeddedScriptSample',
                        file_name='filename.sh',
                        script=r'#!/bin/bash\necho "Hello"\necho "Bye"'),