import urllib.request
import json
import time
import os

# FastAPIサーバーのURL (app_original.py で ngrok によって公開される URL)
# 環境変数 NGROK_URL が設定されていればそれを使用し、なければローカルホストをデフォルトとします。
# 実行前に、app_original.py を実行して表示される ngrok の URL を設定してください。
# 例: export NGROK_URL="https://your-ngrok-url.ngrok.io"
# もしくは、以下の行を直接編集してください。
NGROK_URL = "https://f57c-34-106-143-228.ngrok-free.app"
# NGROK_URL = os.environ.get("NGROK_URL", "http://localhost:8501") # デフォルトはローカル

def health_check(api_url):
    """
    APIサーバーのヘルスチェックを行います (urllib.request を使用)。

    Args:
        api_url (str): APIのベースURL。

    Returns:
        dict: ヘルスチェックの結果。エラーの場合は None。
    """
    url = f"{api_url.rstrip('/')}/health"
    print(f"ヘルスチェックURL: {url}")
    try:
        # GETリクエストを作成
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                # レスポンスボディをデコードしてJSONとしてパース
                data = json.loads(response.read().decode('utf-8'))
                return data
            else:
                print(f"ヘルスチェックエラー: ステータスコード {response.status}")
                return None
    except Exception as e:
        print(f"ヘルスチェック中に例外発生: {e}")
        return None

def generate_text(api_url, prompt, max_new_tokens=512, temperature=0.7, top_p=0.9, do_sample=True):
    """
    APIサーバーにテキスト生成をリクエストします (urllib.request を使用)。

    Args:
        api_url (str): APIのベースURL。
        prompt (str): 生成の元となるプロンプト。
        max_new_tokens (int): 生成する最大トークン数。
        temperature (float): 温度パラメータ。
        top_p (float): top-p サンプリングパラメータ。
        do_sample (bool): サンプリングを行うか。

    Returns:
        dict: 生成結果。エラーの場合は None。
    """
    url = f"{api_url.rstrip('/')}/generate"
    payload = {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "do_sample": do_sample
    }
    # PythonオブジェクトをJSON文字列に変換し、UTF-8でエンコード
    data = json.dumps(payload).encode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json' # サーバーがJSONを返すことを期待
    }

    # POSTリクエストを作成
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    print(f"テキスト生成リクエストURL: {url}")
    # print(f"ペイロード: {payload}") # デバッグ用に必要ならコメント解除

    start_time = time.time()
    try:
        # リクエストを送信し、レスポンスを取得 (タイムアウトを60秒に設定)
        with urllib.request.urlopen(req, timeout=60) as response:
            total_time = time.time() - start_time
            response_body = response.read().decode('utf-8')
            # print(f"レスポンスステータス: {response.status}") # デバッグ用
            # print(f"レスポンスボディ: {response_body}") # デバッグ用

            if response.status == 200:
                result = json.loads(response_body)
                # クライアント側で計測したリクエスト時間を追加
                result["total_request_time"] = total_time
                return result
            else:
                print(f"テキスト生成エラー: ステータスコード {response.status}, ボディ: {response_body}")
                return None
    except urllib.error.HTTPError as e:
        # HTTPエラーが発生した場合
        total_time = time.time() - start_time
        print(f"HTTPエラー発生 ({e.code}): {e.reason}")
        try:
            # エラーレスポンスのボディを読み取る試み
            error_body = e.read().decode('utf-8')
            print(f"エラーレスポンスボディ: {error_body}")
        except Exception as read_err:
            print(f"エラーレスポンスボディの読み取り失敗: {read_err}")
        return None
    except Exception as e:
        # その他の例外が発生した場合
        total_time = time.time() - start_time
        print(f"テキスト生成中に例外発生: {e}")
        return None

if __name__ == "__main__":
    print(f"接続先API URL: {NGROK_URL}")
    if NGROK_URL == "http://localhost:8501" or "your-ngrok-url" in NGROK_URL:
        print("\n警告: NGROK_URLがデフォルトまたはプレースホルダーのままです。")
        print("app_original.py を実行して表示される正しい ngrok URL を設定してください。")
        print("環境変数 'NGROK_URL' を設定するか、このスクリプト内の NGROK_URL 変数を直接編集してください。\n")


    # 1. ヘルスチェックの実行
    print("\n--- ヘルスチェック ---")
    health_status = health_check(NGROK_URL)
    if health_status:
        print(f"ヘルスチェック結果: {health_status}")
        # ヘルスチェックが成功した場合のみテキスト生成へ進む
        if health_status.get("status") == "ok":
            # 2. テキスト生成の実行
            print("\n--- テキスト生成 ---")
            prompt_text = "AIエンジニアリングについて100文字程度で説明してください。"
            generation_result = generate_text(NGROK_URL, prompt_text)

            if generation_result:
                print("\n生成結果:")
                print(f"  生成されたテキスト: {generation_result.get('generated_text', 'N/A')}")
                # app_original.py のレスポンスに含まれるモデル処理時間
                if 'response_time' in generation_result:
                    print(f"  モデル処理時間 (サーバー計測): {generation_result['response_time']:.2f}s")
                # クライアント側で計測したリクエスト時間
                if 'total_request_time' in generation_result:
                     print(f"  総リクエスト時間 (クライアント計測): {generation_result['total_request_time']:.2f}s")
            else:
                print("テキスト生成に失敗しました。サーバーログを確認してください。")
        else:
            print("ヘルスチェックでモデルが利用可能でないと報告されました。サーバーの状態を確認してください。")

    else:
        print("ヘルスチェックに失敗しました。APIサーバーが起動しているか、URLが正しいか確認してください。")
        
# # lambda/index.py
# import json
# import os
# import boto3
# import re  # 正規表現モジュールをインポート
# from botocore.exceptions import ClientError


# # Lambda コンテキストからリージョンを抽出する関数
# def extract_region_from_arn(arn):
#     # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
#     match = re.search('arn:aws:lambda:([^:]+):', arn)
#     if match:
#         return match.group(1)
#     return "us-east-1"  # デフォルト値

# # グローバル変数としてクライアントを初期化（初期値）
# bedrock_client = None

# # モデルID
# MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")

# def lambda_handler(event, context):
#     try:
#         # コンテキストから実行リージョンを取得し、クライアントを初期化
#         global bedrock_client
#         if bedrock_client is None:
#             region = extract_region_from_arn(context.invoked_function_arn)
#             bedrock_client = boto3.client('bedrock-runtime', region_name=region)
#             print(f"Initialized Bedrock client in region: {region}")
        
#         print("Received event:", json.dumps(event))
        
#         # Cognitoで認証されたユーザー情報を取得
#         user_info = None
#         if 'requestContext' in event and 'authorizer' in event['requestContext']:
#             user_info = event['requestContext']['authorizer']['claims']
#             print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
#         # リクエストボディの解析
#         body = json.loads(event['body'])
#         message = body['message']
#         conversation_history = body.get('conversationHistory', [])
        
#         print("Processing message:", message)
#         print("Using model:", MODEL_ID)
        
#         # 会話履歴を使用
#         messages = conversation_history.copy()
        
#         # ユーザーメッセージを追加
#         messages.append({
#             "role": "user",
#             "content": message
#         })
        
#         # Nova Liteモデル用のリクエストペイロードを構築
#         # 会話履歴を含める
#         bedrock_messages = []
#         for msg in messages:
#             if msg["role"] == "user":
#                 bedrock_messages.append({
#                     "role": "user",
#                     "content": [{"text": msg["content"]}]
#                 })
#             elif msg["role"] == "assistant":
#                 bedrock_messages.append({
#                     "role": "assistant", 
#                     "content": [{"text": msg["content"]}]
#                 })
        
#         # invoke_model用のリクエストペイロード
#         request_payload = {
#             "messages": bedrock_messages,
#             "inferenceConfig": {
#                 "maxTokens": 512,
#                 "stopSequences": [],
#                 "temperature": 0.7,
#                 "topP": 0.9
#             }
#         }
        
#         print("Calling Bedrock invoke_model API with payload:", json.dumps(request_payload))
        
#         # invoke_model APIを呼び出し
#         response = bedrock_client.invoke_model(
#             modelId=MODEL_ID,
#             body=json.dumps(request_payload),
#             contentType="application/json"
#         )
        
#         # レスポンスを解析
#         response_body = json.loads(response['body'].read())
#         print("Bedrock response:", json.dumps(response_body, default=str))
        
#         # 応答の検証
#         if not response_body.get('output') or not response_body['output'].get('message') or not response_body['output']['message'].get('content'):
#             raise Exception("No response content from the model")
        
#         # アシスタントの応答を取得
#         assistant_response = response_body['output']['message']['content'][0]['text']
        
#         # アシスタントの応答を会話履歴に追加
#         messages.append({
#             "role": "assistant",
#             "content": assistant_response
#         })
        
#         # 成功レスポンスの返却
#         return {
#             "statusCode": 200,
#             "headers": {
#                 "Content-Type": "application/json",
#                 "Access-Control-Allow-Origin": "*",
#                 "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
#                 "Access-Control-Allow-Methods": "OPTIONS,POST"
#             },
#             "body": json.dumps({
#                 "success": True,
#                 "response": assistant_response,
#                 "conversationHistory": messages
#             })
#         }
        
#     except Exception as error:
#         print("Error:", str(error))
        
#         return {
#             "statusCode": 500,
#             "headers": {
#                 "Content-Type": "application/json",
#                 "Access-Control-Allow-Origin": "*",
#                 "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
#                 "Access-Control-Allow-Methods": "OPTIONS,POST"
#             },
#             "body": json.dumps({
#                 "success": False,
#                 "error": str(error)
#             })
#         }
