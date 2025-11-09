document.addEventListener("DOMContentLoaded", () => {

    // --- CƠ SỞ DỮ LIỆU MÔ PHỎNG (MOCK DATABASE) ---
    const mockProductData = {
        shopee: {
            iphone: {
                name: "iPhone 15 Pro Max 256GB",
                price: "29.500.000đ",
                img: "https://via.placeholder.com/150x150.png?text=iPhone+15",
                avg: "29.800.000đ",
                max: "30.500.000đ",
                min: "29.500.000đ",
                ai_analysis: "Mô hình AI dự đoán giá iPhone 15 sẽ ổn định. Tuy nhiên, phân tích lịch sử cho thấy giá có thể giảm nhẹ vào cuối tháng khi Shopee tung ra voucher 12.12. Khuyến nghị nên chờ thêm 1 tuần để có giá tốt nhất.",
                recommendation: "Nên chờ thêm 5-7 ngày",
                // Dữ liệu biểu đồ lịch sử (30 ngày gần nhất)
                history_30days: [
                    30500000, 30400000, 30300000, 30200000, 30100000, 30000000, 29900000, 29800000,
                    29900000, 30000000, 30100000, 30000000, 29900000, 29800000, 29700000, 29600000,
                    29700000, 29800000, 29900000, 29800000, 29700000, 29600000, 29500000, 29600000,
                    29700000, 29600000, 29500000, 29500000, 29500000, 29500000
                ],
                // Dữ liệu dự đoán (7 ngày tới)
                prediction_7days: [29500000, 29450000, 29400000, 29350000, 29300000, 29250000, 29200000]
            },
            laptop: {
                name: "Laptop Dell XPS 15 9530",
                price: "45.200.000đ",
                img: "https://via.placeholder.com/150x150.png?text=Dell+XPS",
                avg: "45.500.000đ",
                max: "46.000.000đ",
                min: "45.000.000đ",
                ai_analysis: "Dữ liệu cho thấy giá Dell XPS 15 trên Shopee khá biến động. Mô hình dự đoán giá sẽ tăng nhẹ 2-3% trong 7 ngày tới do nhu cầu tăng cao. Đây là thời điểm tốt để mua trước khi giá tăng.",
                recommendation: "Nên mua ngay hôm nay",
                history_30days: [
                    46000000, 45900000, 45800000, 45700000, 45600000, 45500000, 45400000, 45300000,
                    45400000, 45500000, 45600000, 45500000, 45400000, 45300000, 45200000, 45100000,
                    45200000, 45300000, 45400000, 45300000, 45200000, 45100000, 45000000, 45100000,
                    45200000, 45100000, 45000000, 45100000, 45200000, 45200000
                ],
                prediction_7days: [45200000, 45300000, 45400000, 45500000, 45600000, 45700000, 45800000]
            },
            headphone: {
                name: "Tai nghe Sony WH-1000XM5",
                price: "6.990.000đ",
                img: "https://via.placeholder.com/150x150.png?text=Sony+XM5",
                avg: "7.100.000đ",
                max: "7.500.000đ",
                min: "6.990.000đ",
                ai_analysis: "Mô hình LSTM phát hiện một xu hướng giảm giá rõ rệt. Giá dự kiến sẽ tiếp tục giảm trong 3-4 ngày tới. AI khuyến nghị nên đợi thêm.",
                recommendation: "Nên chờ thêm 3-4 ngày",
                history_30days: [
                    7500000, 7450000, 7400000, 7350000, 7300000, 7250000, 7200000, 7150000,
                    7200000, 7250000, 7300000, 7250000, 7200000, 7150000, 7100000, 7050000,
                    7100000, 7150000, 7200000, 7150000, 7100000, 7050000, 6990000, 7000000,
                    7050000, 7000000, 6990000, 6990000, 6990000, 6990000
                ],
                prediction_7days: [6990000, 6950000, 6900000, 6850000, 6900000, 6950000, 7000000]
            }
        },
        lazada: {
            iphone: {
                name: "iPhone 15 Pro Max 256GB",
                price: "29.750.000đ",
                img: "https://via.placeholder.com/150x150.png?text=iPhone+15",
                avg: "30.000.000đ",
                max: "30.500.000đ",
                min: "29.750.000đ",
                ai_analysis: "Giá trên Lazada có vẻ cao hơn một chút so với đối thủ. Mô hình dự đoán giá sẽ được điều chỉnh giảm trong đợt sale giữa tháng sắp tới. Nên theo dõi và đặt thông báo giá.",
                recommendation: "Nên theo dõi thêm",
                history_30days: [
                    30500000, 30450000, 30400000, 30350000, 30300000, 30250000, 30200000, 30150000,
                    30200000, 30250000, 30300000, 30250000, 30200000, 30150000, 30100000, 30050000,
                    30100000, 30150000, 30200000, 30150000, 30100000, 30050000, 29750000, 29800000,
                    29850000, 29800000, 29750000, 29750000, 29750000, 29750000
                ],
                prediction_7days: [29750000, 29700000, 29650000, 29600000, 29550000, 29500000, 29450000]
            },
            laptop: {
                name: "Laptop Dell XPS 15 9530",
                price: "45.000.000đ",
                img: "https://via.placeholder.com/150x150.png?text=Dell+XPS",
                avg: "45.100.000đ",
                max: "45.800.000đ",
                min: "45.000.000đ",
                ai_analysis: "Giá sản phẩm này trên Lazada đang ở mức thấp nhất trong 30 ngày. Mô hình AI dự đoán giá sẽ không giảm thêm. Khuyến nghị mua ngay.",
                recommendation: "Nên mua ngay",
                history_30days: [
                    45800000, 45700000, 45600000, 45500000, 45400000, 45300000, 45200000, 45100000,
                    45200000, 45300000, 45400000, 45300000, 45200000, 45100000, 45000000, 44900000,
                    45000000, 45100000, 45200000, 45100000, 45000000, 44900000, 45000000, 45000000,
                    45100000, 45000000, 45000000, 45000000, 45000000, 45000000
                ],
                prediction_7days: [45000000, 45000000, 45100000, 45200000, 45300000, 45400000, 45500000]
            },
            headphone: {
                name: "Tai nghe Sony WH-1000XM5",
                price: "7.050.000đ",
                img: "https://via.placeholder.com/150x150.png?text=Sony+XM5",
                avg: "7.150.000đ",
                max: "7.400.000đ",
                min: "7.050.000đ",
                ai_analysis: "Giá trên Lazada đang ổn định. Mô hình dự đoán không có biến động lớn trong 7 ngày tới. Quyết định mua có thể được thực hiện bất cứ lúc nào.",
                recommendation: "Có thể mua bất kỳ lúc nào",
                history_30days: [
                    7400000, 7350000, 7300000, 7250000, 7200000, 7150000, 7100000, 7050000,
                    7100000, 7150000, 7200000, 7150000, 7100000, 7050000, 7100000, 7150000,
                    7100000, 7050000, 7100000, 7050000, 7050000, 7050000, 7050000, 7050000,
                    7050000, 7050000, 7050000, 7050000, 7050000, 7050000
                ],
                prediction_7days: [7050000, 7050000, 7100000, 7100000, 7100000, 7150000, 7150000]
            }
        },
        tiki: {
            iphone: {
                name: "iPhone 15 Pro Max 256GB (Tiki Trading)",
                price: "29.550.000đ",
                img: "https://via.placeholder.com/150x150.png?text=iPhone+15",
                avg: "29.900.000đ",
                max: "30.300.000đ",
                min: "29.550.000đ",
                ai_analysis: "Tiki Trading đang có giá tốt. Dữ liệu lịch sử cho thấy Tiki ít thay đổi giá đột ngột. Mô hình AI dự đoán giá sẽ giữ nguyên. Nếu có voucher, đây là lựa chọn tốt.",
                recommendation: "Nên mua ngay nếu có voucher",
                history_30days: [
                    30300000, 30250000, 30200000, 30150000, 30100000, 30050000, 30000000, 29950000,
                    30000000, 30050000, 30100000, 30050000, 30000000, 29950000, 29900000, 29850000,
                    29900000, 29950000, 30000000, 29950000, 29900000, 29850000, 29550000, 29600000,
                    29650000, 29600000, 29550000, 29550000, 29550000, 29550000
                ],
                prediction_7days: [29550000, 29550000, 29550000, 29550000, 29600000, 29600000, 29650000]
            },
            laptop: {
                name: "Laptop Dell XPS 15 9530",
                price: "45.300.000đ",
                img: "https://via.placeholder.com/150x150.png?text=Dell+XPS",
                avg: "45.400.000đ",
                max: "45.900.000đ",
                min: "45.300.000đ",
                ai_analysis: "Giá trên Tiki ổn định. Mô hình dự đoán không có biến động lớn. AI khuyến nghị nên so sánh thêm với các sàn khác trước khi quyết định.",
                recommendation: "Nên so sánh thêm",
                history_30days: [
                    45900000, 45800000, 45700000, 45600000, 45500000, 45400000, 45300000, 45400000,
                    45500000, 45600000, 45500000, 45400000, 45300000, 45400000, 45500000, 45400000,
                    45300000, 45400000, 45500000, 45400000, 45300000, 45300000, 45300000, 45300000,
                    45300000, 45300000, 45300000, 45300000, 45300000, 45300000
                ],
                prediction_7days: [45300000, 45300000, 45400000, 45400000, 45500000, 45500000, 45600000]
            },
            headphone: {
                name: "Tai nghe Sony WH-1000XM5",
                price: "6.950.000đ",
                img: "https://via.placeholder.com/150x150.png?text=Sony+XM5",
                avg: "7.000.000đ",
                max: "7.200.000đ",
                min: "6.950.000đ",
                ai_analysis: "Giá sản phẩm này trên Tiki đang ở mức thấp nhất thị trường. Mô hình LSTM dự đoán đây là 'đáy' của giá và có thể tăng trở lại sau 2-3 ngày. Khuyến nghị mua ngay lập tức.",
                recommendation: "MUA NGAY! Giá tốt nhất",
                history_30days: [
                    7200000, 7150000, 7100000, 7050000, 7000000, 6950000, 7000000, 7050000,
                    7100000, 7150000, 7100000, 7050000, 7000000, 6950000, 7000000, 7050000,
                    7000000, 6950000, 7000000, 6950000, 6950000, 6950000, 6950000, 6950000,
                    6950000, 6950000, 6950000, 6950000, 6950000, 6950000
                ],
                prediction_7days: [6950000, 6950000, 7000000, 7050000, 7100000, 7150000, 7200000]
            }
        }
    };

    // Dữ liệu so sánh giá giữa các sàn
    const comparisonData = {
        iphone: {
            shopee: "29.500.000đ",
            lazada: "29.750.000đ",
            tiki: "29.550.000đ",
            best: "shopee"
        },
        laptop: {
            shopee: "45.200.000đ",
            lazada: "45.000.000đ",
            tiki: "45.300.000đ",
            best: "lazada"
        },
        headphone: {
            shopee: "6.990.000đ",
            lazada: "7.050.000đ",
            tiki: "6.950.000đ",
            best: "tiki"
        }
    };
    // --- KẾT THÚC CƠ SỞ DỮ LIỆU MÔ PHỎNG ---


    // Lấy các phần tử DOM
    const siteSelect = document.getElementById("site-select");
    const productSelect = document.getElementById("product-select");
    const loadDataBtn = document.getElementById("load-data-btn");
    const predictBtn = document.getElementById("predict-btn");

    const productInfoDiv = document.getElementById("product-info");
    const productNameEl = document.getElementById("product-name");
    const productPriceEl = document.getElementById("product-price");
    const productSiteEl = document.getElementById("product-site");
    const productImageEl = document.getElementById("product-image");

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
    
    let currentData = null;

    // --- HÀM VẼ BIỂU ĐỒ (MÔ PHỎNG) ---
    function drawHistoricalChart(data) {
        const chartHeight = 300;
        const chartWidth = historicalChartEl.offsetWidth - 40;
        const maxPrice = Math.max(...data);
        const minPrice = Math.min(...data);
        const priceRange = maxPrice - minPrice;

        let svgContent = `
            <svg width="${chartWidth}" height="${chartHeight}" style="margin: 20px;">
                <defs>
                    <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#667eea;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#667eea;stop-opacity:0" />
                    </linearGradient>
                </defs>
        `;

        // Vẽ đường line chart
        let pathData = "M ";
        data.forEach((price, index) => {
            const x = (index / (data.length - 1)) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            pathData += `${x},${y} `;
        });

        // Vẽ area dưới đường
        let areaPath = pathData + `L ${chartWidth},${chartHeight} L 0,${chartHeight} Z`;
        svgContent += `<path d="${areaPath}" fill="url(#chartGradient)" />`;

        // Vẽ đường line
        svgContent += `<path d="${pathData}" fill="none" stroke="#667eea" stroke-width="3" />`;

        // Vẽ các điểm
        data.forEach((price, index) => {
            const x = (index / (data.length - 1)) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            svgContent += `<circle cx="${x}" cy="${y}" r="4" fill="#667eea" />`;
        });

        svgContent += `</svg>`;
        historicalChartEl.innerHTML = svgContent;
    }

    function drawPredictionChart(historicalData, predictionData) {
        const combinedData = [...historicalData.slice(-7), ...predictionData];
        const chartHeight = 200;
        const chartWidth = predictionChartEl.offsetWidth - 40;
        const maxPrice = Math.max(...combinedData);
        const minPrice = Math.min(...combinedData);
        const priceRange = maxPrice - minPrice;

        let svgContent = `
            <svg width="${chartWidth}" height="${chartHeight}" style="margin: 20px;">
                <defs>
                    <linearGradient id="predGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#10b981;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#10b981;stop-opacity:0" />
                    </linearGradient>
                </defs>
        `;

        // Vẽ đường lịch sử (7 ngày gần nhất)
        let histPath = "M ";
        historicalData.slice(-7).forEach((price, index) => {
            const x = (index / (combinedData.length - 1)) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            histPath += `${x},${y} `;
        });
        svgContent += `<path d="${histPath}" fill="none" stroke="#667eea" stroke-width="2" stroke-dasharray="5,5" />`;

        // Vẽ đường dự đoán
        let predPath = "M ";
        combinedData.slice(6).forEach((price, index) => {
            const x = ((index + 6) / (combinedData.length - 1)) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            predPath += `${x},${y} `;
        });

        let predArea = predPath + `L ${chartWidth},${chartHeight} L ${(6 / (combinedData.length - 1)) * chartWidth},${chartHeight} Z`;
        svgContent += `<path d="${predArea}" fill="url(#predGradient)" />`;
        svgContent += `<path d="${predPath}" fill="none" stroke="#10b981" stroke-width="3" />`;

        // Vẽ điểm dự đoán
        combinedData.slice(6).forEach((price, index) => {
            const x = ((index + 6) / (combinedData.length - 1)) * chartWidth;
            const y = chartHeight - ((price - minPrice) / priceRange) * (chartHeight - 40);
            svgContent += `<circle cx="${x}" cy="${y}" r="4" fill="#10b981" />`;
        });

        svgContent += `</svg>`;
        predictionChartEl.innerHTML = svgContent;
    }

    // --- HÀM CẬP NHẬT SO SÁNH GIÁ ---
    function updateComparison() {
        const product = productSelect.value;
        const comparison = comparisonData[product];
        
        const cards = document.querySelectorAll('.comparison-card');
        cards[0].querySelector('.comparison-price').textContent = comparison.shopee;
        cards[1].querySelector('.comparison-price').textContent = comparison.lazada;
        cards[2].querySelector('.comparison-price').textContent = comparison.tiki;

        // Xóa class best-price cũ
        cards.forEach(card => card.classList.remove('best-price'));
        
        // Thêm badge "Tốt nhất" cho sàn có giá tốt nhất
        const bestIndex = comparison.best === 'shopee' ? 0 : comparison.best === 'lazada' ? 1 : 2;
        cards[bestIndex].classList.add('best-price');
        
        // Xóa badge cũ
        cards.forEach(card => {
            const oldBadge = card.querySelector('.badge-best');
            if (oldBadge) oldBadge.remove();
        });
        
        // Thêm badge mới
        const badge = document.createElement('span');
        badge.className = 'badge badge-best';
        badge.innerHTML = '<i class="fas fa-crown"></i> Tốt nhất';
        cards[bestIndex].appendChild(badge);

        comparisonSection.style.display = "block";
    }

    // --- HÀM TẢI DỮ LIỆU SẢN PHẨM ---
    function fetchMockProductData() {
        const site = siteSelect.value;
        const product = productSelect.value;
        
        // Hiển thị loading
        loadDataBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang tải...';
        loadDataBtn.disabled = true;
        
        setTimeout(() => {
            currentData = mockProductData[site][product];
            
            // 1. Hiển thị thông tin sản phẩm
            productNameEl.textContent = currentData.name;
            productPriceEl.textContent = currentData.price;
            productSiteEl.textContent = siteSelect.options[siteSelect.selectedIndex].text;
            productImageEl.src = currentData.img;
            productInfoDiv.style.display = "flex";

            // 2. Hiển thị thông số phân tích
            avgPriceEl.textContent = currentData.avg;
            maxPriceEl.textContent = currentData.max;
            minPriceEl.textContent = currentData.min;
            analysisMetricsDiv.style.display = "block";

            // 3. Vẽ biểu đồ lịch sử
            drawHistoricalChart(currentData.history_30days);

            // 4. Cập nhật so sánh giá
            updateComparison();

            // 5. Hiển thị nút "Dự báo"
            predictBtn.style.display = "flex";

            // 6. Ẩn kết quả dự báo cũ
            predictionResultsDiv.style.display = "none";

            // Khôi phục nút
            loadDataBtn.innerHTML = '<i class="fas fa-search"></i> <span>Phân tích ngay</span>';
            loadDataBtn.disabled = false;

        }, 800);
    }

    // --- HÀM DỰ ĐOÁN ---
    function fetchMockPrediction() {
        if (!currentData) return;

        predictBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Đang chạy AI...</span>';
        predictBtn.disabled = true;

        setTimeout(() => {
            // 1. Hiển thị card kết quả
            predictionResultsDiv.style.display = "block";
            
            // 2. Vẽ biểu đồ dự đoán
            drawPredictionChart(currentData.history_30days, currentData.prediction_7days);
            
            // 3. Hiển thị giải thích AI
            aiExplanationEl.innerHTML = `<p>${currentData.ai_analysis}</p>`;
            
            // 4. Hiển thị khuyến nghị
            recommendationEl.textContent = currentData.recommendation;

            // 5. Khôi phục nút
            predictBtn.innerHTML = '<i class="fas fa-robot"></i> <span>Xem Dự báo AI</span> <span class="predict-subtitle">Dự đoán 7 ngày tới</span>';
            predictBtn.disabled = false;

            // Scroll đến kết quả
            predictionResultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        }, 1500);
    }

    // Gán sự kiện
    loadDataBtn.addEventListener("click", fetchMockProductData);
    predictBtn.addEventListener("click", fetchMockPrediction);
});