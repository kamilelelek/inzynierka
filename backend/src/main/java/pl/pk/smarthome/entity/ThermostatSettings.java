package pl.pk.smarthome.entity;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// Nastawy regulatora z histerezą (jeden wiersz)
@Entity
@Table(name = "thermostat_settings")
@Getter
@Setter
@NoArgsConstructor
public class ThermostatSettings {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false)
	private boolean enabled;

	@Column(nullable = false)
	private Double targetTemperature;

	@Column(nullable = false)
	private Double hysteresis;

	private Instant updatedAt;

}
