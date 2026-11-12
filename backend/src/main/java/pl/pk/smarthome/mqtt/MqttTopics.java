package pl.pk.smarthome.mqtt;

import java.util.Optional;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.springframework.stereotype.Component;
import pl.pk.smarthome.config.MqttProperties;

// Struktura topiców: home/<hubId>/<urządzenie>/<typ> (zgodnie z hubem na Pi)
@Component
public class MqttTopics {

	private final String base;
	private final Pattern deviceStatePattern;

	public MqttTopics(MqttProperties properties) {
		this.base = "home/" + properties.hubId();
		this.deviceStatePattern = Pattern.compile(Pattern.quote(base) + "/([a-z0-9_-]+)/state");
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

	// home/hub1/led/state -> "led"
	public Optional<String> deviceCodeFromStateTopic(String topic) {
		Matcher matcher = deviceStatePattern.matcher(topic);
		return matcher.matches() ? Optional.of(matcher.group(1)) : Optional.empty();
	}

}
