"""运动传感器组件"""

import logging
import voluptuous as vol
import cv2
import requests
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_SENSOR = 'sensor'
CONF_SCAN_INTERVAL = 'scan_interval'
CONF_NAME = 'name'
CONF_DETECT_URL = 'detect_url'
CONF_CAMERA_URL = 'camera_url'
DEFAULT_SCAN_INTERVAL = 30

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SENSOR): cv.entity_id,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_DETECT_URL): cv.string,
    vol.Optional(CONF_CAMERA_URL): cv.string,

    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(cv.time_period, cv.positive_timedelta),
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """设置运动传感器平台。"""

    sensor_id = config[CONF_SENSOR]
    scan_interval = config[CONF_SCAN_INTERVAL]
    sensor_name = config[CONF_NAME]
    detect_url = config[CONF_DETECT_URL]
    camera_url = config[CONF_CAMERA_URL]
    async_add_entities(
        [CameraMotionSensor(sensor_id, sensor_name, detect_url, camera_url)], True)
    async_track_time_interval(
        hass, lambda arg: self.async_schedule_update_ha_state(True), scan_interval)


class CameraMotionSensor(BinarySensorEntity):
    """运动传感器实体的表示。"""
    NOT_RECON = 0
    EXISTS = 1
    NOT_EXISTS = 2

    def __init__(self, sensor_id, name, detect_url, camera_url):
        """初始化运动传感器实体。"""
        self._sensor_id = sensor_id
        self._name = name
        self._detect_url = detect_url
        self._camera_url = camera_url
        self._state = False
        self._unique_id = "camera_detect"

    @property
    def name(self):
        """返回传感器的名称。"""
        return self._name

    @property
    def is_on(self):
        """返回传感器是否打开。"""
        return self._state

    async def async_update(self):
        """更新传感器状态。"""
        # 在这里，您需要检查您的运动传感器并相应地更新实体的状态。
        # 例如，如果检测到运动，则可以将状态设置为 True；否则为 False。
        # 有关更新二进制传感器实体的更多信息，请参见 Home Assistant 文档。

        # 要访问另一个实体的信息，您可以使用 'hass' 对象：
        # entity_id = "sensor.temperature"
        # temperature = hass.states.get(entity_id).state
        # self._state = temperature > 25
        person_status = await self.detectPerson()
        if person_status == CameraMotionSensor.EXISTS:
            self.state = 'on'
        else :
            self.state = 'off'

    async def async_turn_on(self, **kwargs):
        """打开传感器。"""
        # 在这里，您需要定义如何打开您的运动传感器（如果适用）。
        # 例如，您可能会向连接的设备发送命令以启用运动检测。
        # 有关定义服务调用的更多信息，请参见 Home Assistant 文档。

        # 要调用服务，您也可以使用 'hass' 对象：
        # entity_id = "light.bedroom"
        # await hass.services.async_call("light", "turn_on", {"entity_id": entity_id})

    async def async_turn_off(self, **kwargs):
        """关闭传感器。"""
        # 在这里，您需要定义如何关闭您的运动传感器（如果适用）。
        # 例如，您可能会向连接的设备发送命令以禁用运动检测。
        # 有关定义服务调用的更多信息，请参见 Home Assistant 文档。

    def detect_get_person(self, image_bytes):
        response = requests.post(
            url=self._detect_url,
            files={"image": image_bytes.tobytes()},
            data={"min_confidence": 0.5},
        ).json()
        if response != []:
            for object in response["predictions"]:
                if object["label"] == 'person':
                    return CameraMotionSensor.EXISTS
            return CameraMotionSensor.NOT_EXISTS
        else:
            return CameraMotionSensor.NOT_RECON

    async def detectPerson(self):
        not_exists_count = 0
        capture = cv2.VideoCapture(
            self._camera_url
        )
        while True:
            ret, frame = capture.read()
            index += 1
            person_flag = False
            if ret:
                # cv2.imwrite(("test" + index.__str__() + ".png"), frame)
                ret2, image_bytes = cv2.imencode(".jpg", frame)
                # print(image_bytes)
                status = self.detect_get_person(image_bytes)
                if status == CameraMotionSensor.EXISTS:
                    not_exists_count = 0
                    _LOGGER.info("exists person")
                    return CameraMotionSensor.EXISTS
                if status == CameraMotionSensor.NOT_EXISTS:
                    if not_exists_count >= 5:
                        _LOGGER.info("no person")
                        return CameraMotionSensor.NOT_EXISTS
                    else:
                        not_exists_count += 1
                if status == CameraMotionSensor.NOT_RECON:
                    _LOGGER.info("not reconized")
            # After the loop release the cap detectionect
        capture.release()
        # Destroy all the windows
        cv2.destroyAllWindows()
