document.addEventListener("DOMContentLoaded", () => {
    const API_BASE = "";

    const siteSelect = document.getElementById("site-select");
    const productSelect = document.getElementById("product-select");
    const loadDataBtn = document.getElementById("load-data-btn");
    const predictBtn = document.getElementById("predict-btn");

    const productInfoDiv = document.getElementById("product-info");
    const productNameEl = document.getElementById("product-name");
    const productPriceEl = document.getElementById("product-price");
    const productSiteEl = document.getElementById("product-site");
    const productImageEl = document.getElementById("product-image");
    const updateTimeEl = document.getElementById("update-time");
    const productRatingEl = document.getElementById("product-rating");

    const analysisMetricsDiv = document.getElementById("analysis-metrics");
    const avgPriceEl = document.getElementById("avg-price");
    const maxPriceEl = document.getElementById("max-price");
    const minPriceEl = document.getElementById("min-price");

    const predictionResultsDiv = document.getElementById("prediction-results");
    const aiExplanationEl = document.getElementById("ai-explanation");
    const recommendationEl = document.getElementById("recommendation");

    const historicalChartEl = document.getElementById("historical-chart");
    const predictionChartEl = document.getElementById("prediction-chart");

    const comparisonSection = document.querySelector(".comparison-section");
    const comparisonCards = document.querySelectorAll(".comparison-card");
    const forecastDaysSelect = document.getElementById("forecast-days");
    const historyRangeSelect = document.getElementById("history-range-select");

    let catalog = { platforms: [], products: [] };
    let currentMetrics = null;
    let currentPrediction = null;

    const currencyFormatter = new Intl.NumberFormat("vi-VN", {
        style: "currency",
        currency: "VND",
        maximumFractionDigits: 0
    });

    function formatCurrency(value) {
        if (value === null || value === undefined || Number.isNaN(value)) {
            return "--";
        }
        return currencyFormatter.format(value);
    }

    function formatDate(dateString) {
        if (!dateString) return "--";
        return new Date(dateString).toLocaleDateString("vi-VN");
    }

    function showError(message) {
        alert(message || "Đã xảy ra lỗi, vui lòng thử lại.");
    }

    async function fetchJSON(url, options = {}) {
        const opts = { ...options };
        opts.headers = opts.headers || {};
        if (opts.method && opts.method.toUpperCase() !== "GET") {
            opts.headers["Content-Type"] = "application/json";
        }

        const response = await fetch(url, opts);
        if (!response.ok) {
            let errorMessage = "Không thể tải dữ liệu từ máy chủ.";
            try {
                const errorPayload = await response.json();
                if (errorPayload && errorPayload.message) {
                    errorMessage = errorPayload.message;
                }
            } catch (err) {
                // ignore JSON parsing error
            }
            throw new Error(errorMessage);
        }
        return response.json();
    }

    function populateSelect(selectEl, items, formatter) {
        selectEl.innerHTML = "";
        items.forEach(item => {
            const option = document.createElement("option");
            option.value = item.value;
            option.textContent = formatter(item);
            selectEl.appendChild(option);
        });
    }

    async function loadCatalog() {
        try {
            const data = await fetchJSON(`${API_BASE}/api/catalog`);
            catalog = data;

            const platformOptions = catalog.platforms.map(pf => ({
                value: pf,
                label: pf.charAt(0).toUpperCase() + pf.slice(1)
            }));
            populateSelect(siteSelect, platformOptions, item => item.label);

            const productOptions = catalog.products.map(product => ({
                value: product.id,
                label: product.name
            }));
            populateSelect(productSelect, productOptions, item => item.label);

            loadDataBtn.disabled = false;
        } catch (error) {
            showError(error.message);
            loadDataBtn.disabled = true;
        }
    }

    function drawHistoricalChart(historyPoints) {
        if (!historyPoints || historyPoints.length === 0) {
            historicalChartEl.innerHTML = "<p>Chưa có dữ liệu lịch sử.</p>";
            return;
        }

        const chartHeight = 300;
        const chartWidth = Math.max(200, historicalChartEl.offsetWidth - 40);
        const prices = historyPoints.map(point => point.price);
        const maxPrice = Math.max(...prices);
        const minPrice = Math.min(...prices);
        const priceRange = maxPrice - minPrice || 1;
        const dates = historyPoints.map(point => point.date);

        let svgContent = `
            <svg width="${chartWidth}" height="${chartHeight}" style="margin: 20px;">
                <defs>
                    <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#667eea;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#667eea;stop-opacity:0" />
                    </linearGradient>
                </defs>
        `;

        let pathData = "M ";
        const denom = Math.max(1, prices.length - 1);
        prices.forEach((price, index) => {
            const x = (index / denom) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            pathData += `${x},${y} `;
        });

        const areaPath = `${pathData}L ${chartWidth},${chartHeight} L 0,${chartHeight} Z`;
        svgContent += `<path d="${areaPath}" fill="url(#chartGradient)" />`;
        svgContent += `<path d="${pathData}" fill="none" stroke="#667eea" stroke-width="3" />`;

        prices.forEach((price, index) => {
            const x = (index / denom) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            svgContent += `<circle cx="${x}" cy="${y}" r="4" fill="#667eea" />`;
        });

        svgContent += `<line x1="0" y1="${chartHeight - 20}" x2="${chartWidth}" y2="${chartHeight - 20}" stroke="#1f2937" stroke-width="1" />`;
        svgContent += `<line x1="40" y1="0" x2="40" y2="${chartHeight}" stroke="#1f2937" stroke-width="1" />`;
        svgContent += `<text x="0" y="14" fill="#94a3b8">Giá (VND)</text>`;

        const xTicks = [0, Math.floor(prices.length / 2), prices.length - 1].filter(idx => idx >= 0 && idx < prices.length);
        xTicks.forEach(idx => {
            const x = (idx / denom) * chartWidth;
            svgContent += `<line x1="${x}" y1="${chartHeight - 24}" x2="${x}" y2="${chartHeight - 16}" stroke="#475569" stroke-width="1" />`;
            svgContent += `<text x="${x}" y="${chartHeight - 4}" fill="#94a3b8" font-size="12" text-anchor="middle">${dates[idx]}</text>`;
        });

        svgContent += `<text x="${chartWidth}" y="${chartHeight - 2}" fill="#94a3b8" font-size="12" text-anchor="end">Ngày</text>`;

        svgContent += "</svg>";
        historicalChartEl.innerHTML = svgContent;
    }

    function drawPredictionChart(historicalData, predictionData) {
        if (!historicalData || !predictionData || predictionData.length === 0) {
            predictionChartEl.innerHTML = "<p>Chưa có dữ liệu dự đoán.</p>";
            return;
        }

        const safeHistorical = historicalData && historicalData.length > 0
            ? historicalData
            : [predictionData[0]];
        const historySliceSize = Math.min(7, safeHistorical.length);
        const historySlice = safeHistorical.slice(-historySliceSize);
        const combinedData = [...historySlice, ...predictionData];
        const chartHeight = 200;
        const chartWidth = Math.max(200, predictionChartEl.offsetWidth - 40);
        const maxPrice = Math.max(...combinedData);
        const minPrice = Math.min(...combinedData);
        const priceRange = maxPrice - minPrice || 1;

        let svgContent = `
            <svg width="${chartWidth}" height="${chartHeight}" style="margin: 20px;">
                <defs>
                    <linearGradient id="predGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#10b981;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#10b981;stop-opacity:0" />
                    </linearGradient>
                </defs>
        `;

        let histPath = "M ";
        const denom = Math.max(1, combinedData.length - 1);
        historySlice.forEach((price, index) => {
            const x = (index / denom) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            histPath += `${x},${y} `;
        });
        svgContent += `<path d="${histPath}" fill="none" stroke="#667eea" stroke-width="2" stroke-dasharray="5,5" />`;

        let predPath = "M ";
        combinedData.slice(historySlice.length - 1).forEach((price, index) => {
            const x = ((index + historySlice.length - 1) / denom) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            predPath += `${x},${y} `;
        });

        const predArea = `${predPath}L ${chartWidth},${chartHeight} L ${((historySlice.length - 1) / denom) * chartWidth},${chartHeight} Z`;
        svgContent += `<path d="${predArea}" fill="url(#predGradient)" />`;
        svgContent += `<path d="${predPath}" fill="none" stroke="#10b981" stroke-width="3" />`;

        combinedData.slice(historySlice.length - 1).forEach((price, index) => {
            const x = ((index + historySlice.length - 1) / denom) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            svgContent += `<circle cx="${x}" cy="${y}" r="4" fill="#10b981" />`;
        });

        svgContent += `<line x1="0" y1="${chartHeight - 20}" x2="${chartWidth}" y2="${chartHeight - 20}" stroke="#1f2937" stroke-width="1" />`;
        svgContent += `<line x1="40" y1="0" x2="40" y2="${chartHeight}" stroke="#1f2937" stroke-width="1" />`;
        svgContent += `<text x="0" y="14" fill="#94a3b8">Giá (VND)</text>`;
        svgContent += `<text x="${chartWidth}" y="${chartHeight - 2}" fill="#94a3b8" font-size="12" text-anchor="end">Ngày</text>`;

        svgContent += "</svg>";
        predictionChartEl.innerHTML = svgContent;
    }

    function updateComparison(comparison) {
        if (!comparison || !comparison.prices || Object.keys(comparison.prices).length === 0) {
            comparisonSection.style.display = "none";
            return;
        }

        comparisonCards.forEach(card => {
            const platform = card.dataset.platform;
            const price = comparison.prices[platform];
            card.querySelector(".comparison-price").textContent = price ? formatCurrency(price) : "--";
            card.classList.remove("best-price");
            const oldBadge = card.querySelector(".badge-best");
            if (oldBadge) oldBadge.remove();
        });

        if (comparison.best_platform) {
            const bestCard = document.querySelector(`.comparison-card[data-platform="${comparison.best_platform}"]`);
            if (bestCard) {
                bestCard.classList.add("best-price");
                const badge = document.createElement("span");
                badge.className = "badge badge-best";
                badge.innerHTML = '<i class="fas fa-crown"></i> Tốt nhất';
                bestCard.appendChild(badge);
            }
        }

        comparisonSection.style.display = "block";
    }

    function updateProductInfo(data) {
        productNameEl.textContent = data.product.name;
        productPriceEl.textContent = formatCurrency(data.latest_price);
        productSiteEl.textContent = siteSelect.options[siteSelect.selectedIndex].textContent.trim();
        productImageEl.src = data.product.image;
        productInfoDiv.style.display = "flex";
        updateTimeEl.textContent = formatDate(data.last_updated);
        productRatingEl.textContent = data.rating ? `${Number(data.rating).toFixed(1)}/5` : "--";
    }

    function updateMetrics(data) {
        avgPriceEl.textContent = formatCurrency(data.stats.avg_price);
        maxPriceEl.textContent = formatCurrency(data.stats.max_price);
        minPriceEl.textContent = formatCurrency(data.stats.min_price);
        analysisMetricsDiv.style.display = "block";
    }

    function setPredictBtnIdleState() {
        if (!predictBtn) return;
        const days = forecastDaysSelect ? forecastDaysSelect.value : "7";
        predictBtn.innerHTML = `
            <i class="fas fa-robot"></i>
            <span>Xem Dự báo AI</span>
            <span class="predict-subtitle">Dự đoán ${days} ngày tới</span>
        `;
        predictBtn.disabled = false;
    }

    async function fetchProductMetrics() {
        if (!productSelect.value || !siteSelect.value) {
            showError("Vui lòng chọn sản phẩm và sàn TMĐT.");
            return;
        }

        predictBtn.style.display = "none";
        predictionResultsDiv.style.display = "none";

        loadDataBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang tải...';
        loadDataBtn.disabled = true;

        try {
            const payload = {
                product_id: productSelect.value,
                platform: siteSelect.value,
                history_days: historyRangeSelect ? parseInt(historyRangeSelect.value, 10) || 30 : 30,
            };
            const data = await fetchJSON(`${API_BASE}/api/metrics`, {
                method: "POST",
                body: JSON.stringify(payload)
            });

            currentMetrics = data;
            currentPrediction = null;

            updateProductInfo(data);
            updateMetrics(data);
            drawHistoricalChart(data.history);
            updateComparison(data.comparison);

            predictBtn.style.display = "flex";
            setPredictBtnIdleState();
        } catch (error) {
            showError(error.message);
        } finally {
            loadDataBtn.innerHTML = '<i class="fas fa-search"></i> <span>Phân tích ngay</span>';
            loadDataBtn.disabled = false;
        }
    }

    async function fetchPrediction() {
        if (!currentMetrics) {
            showError("Vui lòng tải dữ liệu trước khi chạy AI.");
            return;
        }

        predictBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Đang chạy AI...</span>';
        predictBtn.disabled = true;

        try {
            const futureDays = forecastDaysSelect ? parseInt(forecastDaysSelect.value, 10) || 7 : 7;
            const payload = {
                product_id: currentMetrics.product.id,
                platform: currentMetrics.platform,
                future_days: futureDays
            };
            const data = await fetchJSON(`${API_BASE}/api/predict`, {
                method: "POST",
                body: JSON.stringify(payload)
            });

            currentPrediction = data;
            predictionResultsDiv.style.display = "block";

            drawPredictionChart(
                currentMetrics.history.map(point => point.price),
                data.predictions.map(point => point.price)
            );

            aiExplanationEl.innerHTML = `<p>${data.ai_summary}</p>`;
            recommendationEl.textContent = data.recommendation;
            predictionResultsDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } catch (error) {
            showError(error.message);
        } finally {
            setPredictBtnIdleState();
        }
    }

    loadDataBtn.addEventListener("click", fetchProductMetrics);
    predictBtn.addEventListener("click", fetchPrediction);
    if (forecastDaysSelect) {
        forecastDaysSelect.addEventListener("change", () => {
            if (predictBtn && predictBtn.style.display !== "none" && !predictBtn.disabled) {
                setPredictBtnIdleState();
            }
        });
    }
    if (historyRangeSelect) {
        historyRangeSelect.addEventListener("change", () => {
            if (productSelect.value && siteSelect.value) {
                fetchProductMetrics();
            }
        });
    }

    loadCatalog();
});
