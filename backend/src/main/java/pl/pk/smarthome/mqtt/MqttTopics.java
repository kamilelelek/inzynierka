package pl.pk.smarthome.mqtt;

import org.springframework.stereotype.Component;
import pl.pk.smarthome.config.MqttProperties;

// Struktura topiców: home/<hubId>/<urządzenie>/<typ> (zgodnie z hubem na Pi)
@Component
public class MqttTopics {

	private final String base;

	public MqttTopics(MqttProperties properties) {
		this.base = "home/" + properties.hubId();
	}

	public String all() {
		return base + "/#";
	}

	public String status() {
		return base + "/status";
	}

	public String climateTelemetry() {
		return base + "/climate/telemetry";
	}

	public String motionEvent() {
		return base + "/motion/event";
	}

	public String deviceSet(String deviceCode) {
		return base + "/" + deviceCode + "/set";
	}

	public String deviceState(String deviceCode) {
		return base + "/" + deviceCode + "/state";
	}

}
