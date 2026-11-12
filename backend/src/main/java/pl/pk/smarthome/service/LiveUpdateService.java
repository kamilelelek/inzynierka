package pl.pk.smarthome.service;

import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

// Push na dashboard przez STOMP: /topic/climate, /topic/motion, /topic/devices, /topic/hub
@Service
@RequiredArgsConstructor
public class LiveUpdateService {

	public static final String CLIMATE = "/topic/climate";
	public static final String MOTION = "/topic/motion";
	public static final String DEVICES = "/topic/devices";
	public static final String HUB = "/topic/hub";

	private final SimpMessagingTemplate messagingTemplate;

	public void publish(String destination, Object payload) {
		// TODO: messagingTemplate.convertAndSend(...)
	}

}
