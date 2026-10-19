package pl.pk.smarthome.entity;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// Historia zmian stanu urządzeń
@Entity
@Table(name = "device_state_changes")
@Getter
@Setter
@NoArgsConstructor
public class DeviceStateChange {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@ManyToOne(fetch = FetchType.LAZY, optional = false)
	@JoinColumn(name = "device_id")
	private Device device;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false)
	private DeviceState state;

	@Column(nullable = false)
	private Instant changedAt;

}
