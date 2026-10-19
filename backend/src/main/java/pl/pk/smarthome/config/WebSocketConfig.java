package pl.pk.smarthome.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

	@Override
	public void registerStompEndpoints(StompEndpointRegistry registry) {
		// TODO: endpoint /ws (+ allowed origins frontendu)
	}

	@Override
	public void configureMessageBroker(MessageBrokerRegistry registry) {
		// TODO: simple broker na /topic, prefiks aplikacji /app
	}

	// TODO: uwierzytelnianie JWT przy CONNECT (ChannelInterceptor)

}
