package pl.pk.smarthome.config;

import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.integration.channel.DirectChannel;
import org.springframework.integration.core.MessageProducer;
import org.springframework.integration.mqtt.core.DefaultMqttPahoClientFactory;
import org.springframework.integration.mqtt.core.MqttPahoClientFactory;
import org.springframework.integration.mqtt.inbound.MqttPahoMessageDrivenChannelAdapter;
import org.springframework.integration.mqtt.outbound.MqttPahoMessageHandler;
import org.springframework.integration.mqtt.support.DefaultPahoMessageConverter;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.MessageHandler;
import org.springframework.util.StringUtils;
import pl.pk.smarthome.mqtt.MqttTopics;

@Configuration
public class MqttConfig {

	private static final int QOS_RELIABLE = 1;

	@Bean
	public MqttPahoClientFactory mqttClientFactory(MqttProperties properties) {
		MqttConnectOptions options = new MqttConnectOptions();
		options.setServerURIs(new String[] {properties.brokerUrl()});
		if (StringUtils.hasText(properties.username())) {
			options.setUserName(properties.username());
			options.setPassword(properties.password() == null ? new char[0] : properties.password().toCharArray());
		}
		options.setAutomaticReconnect(true);
		options.setCleanSession(true);
		options.setConnectionTimeout(10);
		options.setKeepAliveInterval(30);

		DefaultMqttPahoClientFactory factory = new DefaultMqttPahoClientFactory();
		factory.setConnectionOptions(options);
		return factory;
	}

	@Bean
	public MessageChannel mqttInboundChannel() {
		return new DirectChannel();
	}

	// Osobni klienci MQTT do odbioru i wysyłania (broker wymaga unikalnych client ID).
	@Bean
	public MessageProducer mqttInbound(MqttPahoClientFactory factory, MqttProperties properties, MqttTopics topics) {
		MqttPahoMessageDrivenChannelAdapter adapter =
				new MqttPahoMessageDrivenChannelAdapter(properties.clientId() + "-in", factory, topics.all());
		adapter.setQos(QOS_RELIABLE);
		adapter.setConverter(new DefaultPahoMessageConverter());
		adapter.setCompletionTimeout(5000);
		adapter.setOutputChannel(mqttInboundChannel());
		return adapter;
	}

	@Bean
	public MessageChannel mqttOutboundChannel() {
		return new DirectChannel();
	}

	@Bean
	@ServiceActivator(inputChannel = "mqttOutboundChannel")
	public MessageHandler mqttOutbound(MqttPahoClientFactory factory, MqttProperties properties) {
		MqttPahoMessageHandler handler = new MqttPahoMessageHandler(properties.clientId() + "-out", factory);
		handler.setAsync(true);
		handler.setDefaultQos(QOS_RELIABLE);
		handler.setDefaultRetained(false);
		return handler;
	}

}
