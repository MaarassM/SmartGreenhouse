document.addEventListener("DOMContentLoaded", () => {
    const temperatureReading = document.getElementById("temperature");
    const humidityReading = document.getElementById("humidity");
    const moistureReading = document.getElementById("moisture");
    const waterStatus = document.getElementById("waterStatus");
    const pumpStatus = document.getElementById("pumpStatus");
    const fanStatus = document.getElementById("fanStatus");


    // Funkcija za dohvaćanje senzorskih očitanja
    function fetchReadings() {
        console.log("🔄 Dohvaćam podatke...");
        fetch("http://localhost:3000/api/readings")
            .then(response => {
                if (!response.ok) {
                    throw new Error("❌ Server nije vratio ispravne podatke.");
                }
                return response.json();
            })
            .then(data => {
                console.log("✅ Podaci dohvaćeni:", data);


                temperatureReading.textContent = `${data.temperature}°C`;
                humidityReading.textContent = `${data.humidity}%`;
                moistureReading.textContent = `${data.moisture}`;


                // Status vode
                if (data.water_status === "low") {
                    waterStatus.textContent = "❌ Nema vode";
                    waterStatus.style.color = "red";
                } else if (data.water_status === "ok") {
                    waterStatus.textContent = "✅ Ima vode";
                    waterStatus.style.color = "green";
                } else {
                    waterStatus.textContent = "--";
                    waterStatus.style.color = "gray";
                }


                // Status pumpe
                pumpStatus.textContent = data.pump_status === "on" ? "✅ Uključena" : "❌ Isključena";
                pumpStatus.style.color = data.pump_status === "on" ? "green" : "red";


                // Status ventilatora
                fanStatus.textContent = data.fan_status === "on" ? "✅ Uključeno" : "❌ Isključeno";
                fanStatus.style.color = data.fan_status === "on" ? "green" : "red";
            })
            .catch(error => console.error("❌ Greška pri dohvaćanju senzorskih podataka:", error));
    }


    // Prvo dohvaćanje podataka odmah
    fetchReadings();


    // Periodično dohvaćanje podataka svakih 5 sekundi
    setInterval(fetchReadings, 2000);
});
