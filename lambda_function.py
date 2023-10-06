import boto3
import base64
import io
import cgi
import logging
import traceback


# logger設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# rekognition インスタンスの作成
rekognition = boto3.client('rekognition')

# lambda_handler 関数の定義
def lambda_handler(event, context):
    logger.info(f'Received event = {event}')

    # HTMLフォームからアップロードされた部分はBase64形式でエンコードされた状態で受信するため、bytes型にデコードする
    received_body = base64.b64decode(event['body-json'])
    # cgi.FieldStorageでHTMLフォームを解析できるように、BytesIO オブジェクトを生成する
    body_bytes = io.BytesIO(received_body)

    # cgi.FieldStorageクラスを用いて、フォームの内容を解析する
    environ = {'REQUEST_METHOD': 'POST'}
    headers = {'content-type': event['params']['header']['content-type']}
    form = cgi.FieldStorage(fp=body_bytes, environ=environ, headers=headers)
    # 画像ファイルをbytes型で取得（'uploadfile'は送信時に設定した当該ファイルのnameの値）
    image = form.getvalue('uploadfile')

    # 取得した画像ファイルを、Rekognitionのrecognize_celebritiesメソッドに渡して有名人の検出をする
    response = rekognition.recognize_celebrities(
        Image={'Bytes': image}
    )
    logger.info(f'Rekognition response = {response}')

    try:
        # Rekognition のレスポンスから有名人の名前と信頼度を取り出し、APIのコール元へレスポンスする
        label   = response['CelebrityFaces'][0]
        name    = label['Name']
        conf    = round(label['Face']['Confidence'])
        output  = f'He/She is {name} with {conf}% confidence.'
        logger.info(f'API response = {output}')
        return output

    except IndexError as e:
        # Rekognition のレスポンスから有名人情報を取得出来なかった場合、他の写真にするように伝える。
        logger.info(f"Coudn't detect celebrities in the Photo. Exception = {e}")
        logger.info(traceback.format_exc())
        return "Couldn't detect celebrities in the uploaded photo. Please upload another photo."
