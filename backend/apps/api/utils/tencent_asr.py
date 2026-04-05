import base64
import json
import logging
from django.conf import settings
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models

logger = logging.getLogger(__name__)

class TencentASR:
    def __init__(self):
        config = settings.TENCENT_CLOUD_CONFIG
        self.secret_id = config['SECRET_ID']
        self.secret_key = config['SECRET_KEY']
        self.region = config['REGION']

    def speech_to_text(self, audio_data: bytes, voice_format: str = 'mp3', sample_rate: int = 16000) -> str:
        """
        一句话识别 (SentenceRecognition)
        :param audio_data: 音频二进制数据
        :param voice_format: 格式, 支持 mp3, m4a, wav, pcm
        :param sample_rate: 采样率, 常用 16000 或 8000
        :return: 识别出的文本
        """
        try:
            cred = credential.Credential(self.secret_id, self.secret_key)
            # 配置网络属性，增加超时时间以防止长语音上传超时
            httpProfile = HttpProfile()
            httpProfile.reqTimeout = 60  # 延长至60秒
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile

            client = asr_client.AsrClient(cred, self.region, clientProfile)
            
            # 将音频转为 Base64
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            # 内部保留一个记录
            logger.info(f"ASR Request: size={len(audio_data)}, fmt={voice_format}")

            req = models.SentenceRecognitionRequest()
            params = {
                "EngSerViceType": "16k_zh", 
                "SourceType": 1, 
                "VoiceFormat": voice_format,
                "Data": base64_audio,
                "DataLen": len(audio_data)
            }
            req.from_json_string(json.dumps(params))

            resp = client.SentenceRecognition(req)
            result = json.loads(resp.to_json_string())
            
            return result.get('Result', '')

        except TencentCloudSDKException as err:
            logger.error(f"Tencent ASR API failed: {err}")
            raise err
        except Exception as e:
            logger.error(f"Tencent ASR unexpected error: {e}")
            raise e
