import requests
import urllib.parse
import json
import requests
import os
from requests.auth import HTTPBasicAuth

'''
 * オンプレJIRAサーバーのサービスデスクに上がったチケットを
 * 割り振られた担当者に対してSlack通知する
'''
def main:
  # 検索したいプロジェクト名とステータス
  project = 'project_name'
  status = 'status'

  # URLエンコード
  encode_project = urllib.parse.quote(project)
  encode_status = urllib.parse.quote(status)

  # チケット情報取得API
  # hostnameは各環境に合わせて変更
  api = "https://hostname/rest/api/2/search?maxResults=100&jql=project=%s+and+status=%s" % (encode_project, encode_status)

  # Basic認証（usernameとpasswordはJIRAアカウントを利用）
  req = requests.get(api, auth=HTTPBasicAuth('username', 'password'))
  json_contents = req.json()

  message = "以下JIRAチケットを確認してください。\n\n"
  message_personal = {}
  assignee_list = []

  if json_contents['issues']:
      for fields in json_contents['issues']:
          web_link = ''
          # カスタムフィールドは適宜変更
          # リダイレクトするためにURLを取得
          if fields['fields']['customfield_xxxx'] is not None:
              web_link = fields['fields']['customfield_xxxx']['_links']['web']

          # チケット担当者の取得
          if fields['fields']['assignee']['name'] is not None:
              assignee_name = fields['fields']['assignee']['name']
          else:
              assignee_name = '担当者未割り当て'
          # チケットの題名
          summary = fields['fields']['summary']

          assignee_list.append(assignee_name)

          # リンクがある場合はSlackのメッセージででsummary表示しリダイレクト用リンクを埋め込む
          # 担当者毎のメッセージを作り込む
          if web_link == '':
              if assignee_name in message_personal:
                  message_personal[assignee_name] += summary + "\n"
              else:
                  message_personal[assignee_name] = '@' + assignee_name + "\n" + summary + "\n"
          else:
              if assignee_name in message_personal:
                  message_personal[assignee_name] += '<' + web_link + '|' + summary + ">\n"
              else:
                  message_personal[assignee_name] = '@' + assignee_name + "\n" + '<' + web_link + '|' + summary + ">\n"


          contents = ''
          assignee_list_uniq = list(set(assignee_list))
          for user in assignee_list_uniq:
              contents += message_personal[user] + "\n"

      send_slack_message('channel_name', 'title', message + contents, ':icon:')


'''
 * Slackでメッセージを送信する
 * @param channel_name:送信先チャンネル名（個人名設定可）
 * @param title:送信時のタイトル
 * @param message:送信内容
 * @param icon:アイコン
'''
def send_slack_message(channel_name, title, message, icon):
    # 作成したwebhookのURLを設定
    SLACK_WEBHOOK_URL = 'webhook_url'

    jsonData = {
        'channel':channel_name,
        'username':user_name,
        'text':message,
        'icon_emoji':icon,
        'link_names':'true'
    }

    content = json.dumps(jsonData)

    requests.post(SLACK_WEBHOOK_URL, data=content)
