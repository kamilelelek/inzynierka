package pl.pk.smarthome.config;

import org.springframework.context.annotation.Configuration;

@Configuration
public class MqttConfig {

	// TODO: MqttPahoClientFactory (brokerUrl, login, hasło, automatic reconnect)
	// TODO: kanał "mqttInboundChannel" + MqttPahoMessageDrivenChannelAdapter subskrybujący home/{hubId}/#
	// TODO: kanał "mqttOutboundChannel" + MqttPahoMessageHandler (@ServiceActivator)

}
