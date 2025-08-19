<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>단일 질병 그래프</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.0/cytoscape.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/layout-base/layout-base.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cose-base/cose-base.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-fcose/cytoscape-fcose.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            display: flex;
            font-family: Arial, sans-serif;
            height: 100vh;
            overflow: hidden;
        }
        #sidebar {
            width: 320px;
            background: #f4f4f4;
            padding: 20px;
            overflow-y: auto;
            border-right: 2px solid #ddd;
        }
        #sidebar h1 {
            font-size: 22px;
            margin-bottom: 15px;
            text-align: center;
        }
        .filter-info, .filter-section {
            font-size: 14px;
            margin-bottom: 15px;
            padding: 10px;
            background: #fff;
            border-radius: 5px;
            box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
        }
        .filter-info p, .filter-section label {
            margin: 5px 0;
            font-weight: bold;
        }
        button {
            width: 100%;
            padding: 10px;
            font-size: 16px;
            margin-top: 10px;
            cursor: pointer;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
        }
        button:hover {
            background-color: #0056b3;
        }
        #cy {
            flex: 1;
            height: 100vh;
        }
        input[type="range"], input[type="number"], select {
            width: 100%;
            padding: 8px;
            margin-top: 5px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .slider-container {
            margin-top: 15px;
            text-align: center;
        }
        .slider-value {
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            margin-top: 5px;
        }
    </style>
</head>
<body>

    <!-- 왼쪽 사이드바 -->
    <div id="sidebar">
        <h1>단일 질병 그래프</h1>

        {% if error_message %}
            <p class="error-message" style="color: red; font-size: 16px; font-weight: bold;">{{ error_message }}</p>
        {% else %}
            <div class="filter-info">
                <p><b>선택한 질병:</b> {{ disease_code }}</p>
                <p><b>Follow-Up 기간:</b> <span id="follow-up-value">{{ follow_up }}</span></p>
                <p><b>RR 값 범위:</b> <span id="rr-value">{{ rr_min }} ~ {{ rr_max }}</span></p>
                <p><b>Chi-Square P-Values:</b> ≤ <span id="chisq-value">{{ chisq_p }}</span></p>
                <p><b>Fisher P-Values:</b> ≤ <span id="fisher-value">{{ fisher_p }}</span></p>
            </div>
        {% endif %}

        <!-- Follow-Up 기간 조절 슬라이드 바 -->
        <div class="slider-container">
            <label for="follow-up-slider"><b>Follow-Up 기간 조정</b></label>
            <input type="range" id="follow-up-slider" min="1" max="10" step="1" value="{{ follow_up }}" oninput="updateFollowUpValue(this.value)">
            <p class="slider-value">선택된 값: <span id="follow-up-display">{{ follow_up }}</span></p>
        </div>

        <br/>

        <!-- RR Value 선택 -->
        <div class="filter-section">
            <label for="rr-min">RR Values Min:</label>
            <input type="number" id="rr-min" step="0.1" value="{{ rr_min }}" oninput="updateRRValue()">
            <label for="rr-max">RR Values Max:</label>
            <input type="number" id="rr-max" step="0.1" value="{{ rr_max }}" oninput="updateRRValue()">
        </div>

        <!-- P-Value 선택 -->
        <div class="filter-section">
            <label for="chisq-p">Chi-Square P-Values:</label>
            <select id="chisq-p" onchange="updateChisqValue()">
                <option value="0.5">≤ 0.5</option>
                <option value="0.05">≤ 0.05</option>
                <option value="0.005">≤ 0.005</option>
                <option value="0.0001">≤ 0.0001</option>
            </select>

            <label for="fisher-p">Fisher P-Values:</label>
            <select id="fisher-p" onchange="updateFisherValue()">
                <option value="0.5">≤ 0.5</option>
                <option value="0.05">≤ 0.05</option>
                <option value="0.005">≤ 0.005</option>
                <option value="0.0001">≤ 0.0001</option>
            </select>
        </div>

        <button onclick="window.location.href='{% url 'disease_select' %}'">뒤로 가기</button>
    </div>

    <!-- 오른쪽 그래프 -->
    <div id="cy"></div>

    <script>
        var elements = {
            nodes: {{ nodes|safe }},
            edges: {{ edges|safe }}
        };

        var cy = cytoscape({
            container: document.getElementById('cy'),
            elements: elements,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#666',
                        'label': 'data(id)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'color': '#fff',
                        'font-size': '12px',
                        'width': '30px',
                        'height': '30px',
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 'mapData(weight, 0, 10, 0.5, 3)',
                        'line-color': '#ccc',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#ccc',
                        'curve-style': 'bezier'
                    }
                }
            ],
            layout: {
                name: 'fcose',
                nodeRepulsion: 20000,
                idealEdgeLength: 250,
                gravity: 0.001,
                numIter: 5000,
                avoidOverlap: true,
                padding: 50,
                nodeSeparation: 100,
                uniformNodeDimensions: false,
                randomize: true,
                fit: true
            }
        });

        function updateFollowUpValue(value) {
            document.getElementById('follow-up-display').innerText = value;
            document.getElementById('follow-up-value').innerText = value;
        }

        function updateRRValue() {
            let min = document.getElementById("rr-min").value;
            let max = document.getElementById("rr-max").value;
            document.getElementById("rr-value").innerText = min + " ~ " + max;
        }

        function updateChisqValue() {
            document.getElementById("chisq-value").innerText = document.getElementById("chisq-p").value;
        }

        function updateFisherValue() {
            document.getElementById("fisher-value").innerText = document.getElementById("fisher-p").value;
        }
    </script>

</body>
</html>
