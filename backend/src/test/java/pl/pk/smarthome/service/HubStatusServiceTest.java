package pl.pk.smarthome.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;

import java.time.Instant;

import org.junit.jupiter.api.Test;
import pl.pk.smarthome.mqtt.message.HubStatusMessage;

class HubStatusServiceTest {

	private final HubStatusService service = new HubStatusService(mock(LiveUpdateService.class));

	@Test
	void offlineUntilFirstMessage() {
		assertThat(service.getStatus().online()).isFalse();
		assertThat(service.getStatus().since()).isNull();
	}

	@Test
	void onlineThenLastWill() {
		Instant ts = Instant.parse("2026-10-19T12:00:00Z");
		service.handleStatus(new HubStatusMessage("online", ts));
		assertThat(service.getStatus().online()).isTrue();
		assertThat(service.getStatus().since()).isEqualTo(ts);

		service.handleStatus(new HubStatusMessage("offline", null));
		assertThat(service.getStatus().online()).isFalse();
		assertThat(service.getStatus().since()).isAfter(ts);
	}

	@Test
	void unknownStateIsIgnored() {
		service.handleStatus(new HubStatusMessage("online", Instant.now()));
		service.handleStatus(new HubStatusMessage("rebooting", Instant.now()));
		assertThat(service.getStatus().online()).isTrue();
	}

}
