
const elements = {
    nodes: window.graphData.nodes,
    edges: window.graphData.edges
};

const diseaseList = document.querySelectorAll('.disease-item');
const searchBar = document.getElementById('search-bar');
const cyContainer = document.getElementById('cy');
const nodeInfo = document.getElementById('node-info');

const cy = cytoscape({
    container: cyContainer,
    elements: elements,
    style: [
        {
            selector: 'node',
            style: {
                'background-color': '#666',
                'shape': 'rectangle',
                'label': 'data(id)',
                'width': 'data(width)',
                'height': 'data(height)',
                'text-valign': 'center',
                'color': '#000',
                'font-size': '15px'
            }
        },
        {
            selector: 'edge',
            style: {
                'width': 'mapData(weight, 0, 10, 0.5, 2)',
                'line-color': '#ccc',
                'target-arrow-color': '#ccc',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'arrow-scale': 0.7
            }
        },
        {
            selector: '.highlighted-node',
            style: {
                'background-color': '#FF8C00',
                'z-index': 9999
            }
        },
        {
            selector: '.incoming',
            style: {
                'line-color': '#FF0000',
                'target-arrow-color': '#FF0000'
            }
        },
        {
            selector: '.outgoing',
            style: {
                'line-color': '#0000FF',
                'target-arrow-color': '#0000FF'
            }
        }
    ],
    layout: {
        name: 'fcose',
        animate: true,
        nodeRepulsion: 80000,
        idealEdgeLength: 150,
        gravity: 1,
        nodeSeparation: 100,
        uniformNodeDimensions: false,
        fit: true,
        padding: 30
    },
    zoom: 1,
    pan: { x: 0, y: 0 }
});

cy.on('layoutstop', () => {
    cy.fit(null, 20);
    cy.zoom(1.4);
    cy.center();
});

cy.on('mouseover', 'node', function (evt) {
    let node = evt.target;
    let nodeId = node.id();
    let diseaseInfo = [...diseaseList].find(d => d.getAttribute('data-code') === nodeId);
    if (diseaseInfo) {
        nodeInfo.innerHTML = `${diseaseInfo.innerHTML}`;
        nodeInfo.style.display = "block";
    }
});

cy.on('mouseout', function (event) {
    if (event.target === cy) {
        nodeInfo.style.display = "none";
    }
});

diseaseList.forEach(item => {
    item.addEventListener('click', () => {
        const diseaseCode = item.getAttribute('data-code');
        focusNode(diseaseCode);
    });
});

searchBar.addEventListener('input', () => {
    const query = searchBar.value.trim().toUpperCase();
    const matchingItems = Array.from(diseaseList).filter(item =>
        item.dataset.code.toUpperCase().includes(query)
    );
    diseaseList.forEach(item => item.style.display = 'none');
    matchingItems.forEach(item => item.style.display = 'block');
});

function focusNode(nodeId) {
    const targetNode = cy.$(`#${nodeId}`);
    if (targetNode.length > 0) {
        cy.elements().removeClass('highlighted-node incoming outgoing incoming-node outgoing-node');
        targetNode.addClass('highlighted-node');
        targetNode.connectedEdges(edge => edge.target().id() === nodeId).forEach(edge => {
            edge.addClass('incoming');
            edge.source().addClass('incoming-node');
        });
        targetNode.connectedEdges(edge => edge.source().id() === nodeId).forEach(edge => {
            edge.addClass('outgoing');
            edge.target().addClass('outgoing-node');
        });
        cy.animate({
            fit: {
                eles: targetNode,
                padding: 430
            },
            duration: 500
        });
    } else {
        alert('그래프에 해당 노드가 없습니다.');
    }
}

cy.on('mouseover', 'node', function (event) {
    const node = event.target;
    cy.elements().removeClass('incoming outgoing incoming-node outgoing-node');
    node.addClass('highlighted-node');
    node.connectedEdges(edge => edge.target().id() === node.id()).forEach(edge => {
        edge.addClass('incoming');
        edge.source().addClass('incoming-node');
    });
    node.connectedEdges(edge => edge.source().id() === node.id()).forEach(edge => {
        edge.addClass('outgoing');
        edge.target().addClass('outgoing-node');
    });
});

cy.on('mouseout', 'node', function (event) {
    const node = event.target;
    node.removeClass('highlighted-node');
    node.connectedEdges(edge => edge.target().id() === node.id()).forEach(edge => {
        edge.removeClass('incoming');
        edge.source().removeClass('incoming-node');
    });
    node.connectedEdges(edge => edge.source().id() === node.id()).forEach(edge => {
        edge.removeClass('outgoing');
        edge.target().removeClass('outgoing-node');
    });
});

// ✅ 그룹 토글 기능 개선 (단절 노드도 숨김)
document.querySelectorAll('.group-toggle').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
        const activeGroups = Array.from(document.querySelectorAll('.group-toggle:checked'))
            .map(cb => cb.dataset.group);

        cy.batch(() => {
            cy.nodes().forEach(n => {
                const group = n.data('group');
                const show = activeGroups.includes(group);
                n.style('display', show ? 'element' : 'none');
            });

            cy.edges().forEach(e => {
                const srcVisible = e.source().style('display') !== 'none';
                const tgtVisible = e.target().style('display') !== 'none';
                e.style('display', (srcVisible && tgtVisible) ? 'element' : 'none');
            });

            cy.nodes().forEach(n => {
                if (n.connectedEdges().filter(e => e.style('display') !== 'none').length === 0) {
                    n.style('display', 'none');
                }
            });
        });
    });
});
const sidebar = document.getElementById("info-sidebar");
const sidebarBody = document.getElementById("sidebar-body");

// 노드 클릭 시 사이드바 열기
cy.on('tap', 'node', function (evt) {
    const node = evt.target;
    const nodeId = node.id();
    const nodeLabel = node.data('label');

    sidebarBody.innerHTML = `<p><strong>노드 코드</strong>: ${nodeId}</p>
                             <p><strong>질병 이름</strong>: ${nodeLabel}</p>
                             <p>로딩 중...</p>`;
    sidebar.classList.add("open");

    fetch(`/network/get_detail_info/?type=node&node_id=${nodeId}`)
        .then(response => response.json())
        .then(json => {
            if (json.error) {
                sidebarBody.innerHTML = `<p><strong>${nodeId}</strong></p><p>${json.error}</p>`;
                return;
            }

            const d = json.data;
            const sex = d.sex || {};
            const age = d.age || {};
            const ctrb = d.ctrb || {};
            const sido = d.sido || {};
            const sexAge = d.sex_age || {};
            const sexCtrb = d.sex_ctrb || {};
            const sexSido = d.sex_sido || {};

            const ageLabels = Object.keys(age);
            const incomeLabels = Object.keys(ctrb);
            const sidoLabels = Object.keys(sido);

            const maleIncome = incomeLabels.map(i => Number(d.sex_ctrb["1"]?.[Number(i)] || 0));
            const femaleIncome = incomeLabels.map(i => Number(d.sex_ctrb["2"]?.[Number(i)] || 0));

            const maleSido = sidoLabels.map(i => Number(d.sex_sido["1"]?.[Number(i)] || 0));
            const femaleSido = sidoLabels.map(i => Number(d.sex_sido["2"]?.[Number(i)] || 0));

            const maleAge = ageLabels.map(i => Number(d.sex_age["1"]?.[Number(i)] || 0));
            const femaleAge = ageLabels.map(i => Number(d.sex_age["2"]?.[Number(i)] || 0));



            sidebarBody.innerHTML = `
                <p><strong>노드 코드:</strong> ${nodeId}</p>
                <p><strong>질병 이름:</strong> ${nodeLabel}</p>
                <div class="pubmed-button-container">
                    <button id="pubmed-button" onclick="loadPubmed('${nodeId}')">관련 논문 보기</button>
                </div>
                <div class="graph-box"><h4>성별 비율</h4><canvas id="genderChart"></canvas></div>
                <div class="graph-box"><h4>연령 분포</h4><canvas id="ageBarChart"></canvas></div>
                <div class="graph-box"><h4>지역 분포</h4><canvas id="sidoChart"></canvas></div>
                <div class="graph-box"><h4>소득 수준 분포</h4><canvas id="incomeChart"></canvas></div>
                <div class="graph-box"><h4>성별 × 연령</h4><canvas id="sexAgeChart"></canvas></div>
                <div class="graph-box"><h4>성별 × 소득</h4><canvas id="sexIncomeChart"></canvas></div>
                <div class="graph-box"><h4>성별 × 지역</h4><canvas id="sexSidoChart"></canvas></div>
            `;

            // 성별 파이차트
            new Chart(document.getElementById('genderChart'), {
                type: 'pie',
                data: {
                    labels: ['남성', '여성'],
                    datasets: [{ data: [sex['1'] || 0, sex['2'] || 0], backgroundColor: ['#4e79a7', '#f28e2b'] }]
                },
                options: { responsive: true }
            });

            // 연령 막대그래프
            new Chart(document.getElementById('ageBarChart'), {
                type: 'bar',
                data: {
                    labels: ageLabels,
                    datasets: [{ label: '연령 분포', data: ageLabels.map(a => age[a]), backgroundColor: '#4e79a7' }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
            //성별+연령별
            new Chart(document.getElementById('sexAgeChart'), {
                type: 'bar',
                data: {
                    labels: ageLabels,
                    datasets: [
                        { label: '남성', data: maleAge, backgroundColor: '#4e79a7' },
                        { label: '여성', data: femaleAge, backgroundColor: '#f28e2b' }
                    ]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
            // 지역 막대그래프
            new Chart(document.getElementById('sidoChart'), {
                type: 'bar',
                data: {
                    labels: sidoLabels,
                    datasets: [{ label: '지역 분포', data: sidoLabels.map(s => sido[s]), backgroundColor: '#f28e2b' }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
            // 성별 + 지역
            new Chart(document.getElementById('sexSidoChart'), {
                type: 'bar',
                data: {
                    labels: sidoLabels,
                    datasets: [
                        { label: '남성', data: maleSido, backgroundColor: '#4e79a7' },
                        { label: '여성', data: femaleSido, backgroundColor: '#f28e2b' }
                    ]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
            // 소득수준 막대그래프
            new Chart(document.getElementById('incomeChart'), {
                type: 'bar',
                data: {
                    labels: incomeLabels,
                    datasets: [{ label: '소득 수준 분포', data: incomeLabels.map(i => ctrb[i]), backgroundColor: '#59a14f' }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });

            // 성별+소득수준
            new Chart(document.getElementById('sexIncomeChart'), {
                type: 'bar',
                data: {
                    labels: incomeLabels,
                    datasets: [
                        { label: '남성', data: maleIncome, backgroundColor: '#4e79a7' },
                        { label: '여성', data: femaleIncome, backgroundColor: '#f28e2b' }
                    ]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });

        })
        .catch(err => {
            console.error("Node info fetch error:", err);
            sidebarBody.innerHTML = `<p><strong>${nodeId}</strong></p><p>정보 불러오기 실패</p>`;
        });
});






// 엣지 클릭 시 사이드바 열기
cy.on('tap', 'edge', function (evt) {
    const edge = evt.target;
    const source = edge.source().id();
    const target = edge.target().id();

    const sourceLabel = edge.source().data('label');
    const targetLabel = edge.target().data('label');

    const followUp = window.graphData.follow_up;
    const rrMin = window.graphData.rr_min;
    const rrMax = window.graphData.rr_max;
    const chisq = window.graphData.chisq;
    const fisher = window.graphData.fisher;

sidebarBody.innerHTML = `
        <p><strong>Edge:</strong> ${source} (${sourceLabel}) → ${target} (${targetLabel})</p>
        <p>세부정보 불러오는 중...</p>
    `;
sidebar.classList.add("open");

const url = `/network/get_detail_info/?type=edge&source=${source}&target=${target}&follow_up=${followUp}&rr_values_min=${rrMin}&rr_values_max=${rrMax}&chisq_p_values=${chisq}&fisher_p_values=${fisher}`;

fetch(url)
    .then(response => response.json())
    .then(json => {
        if (json.error) {
            sidebarBody.innerHTML = `<p><strong>Edge</strong>: ${source} → ${target}</p><p>${json.error}</p>`;
            return;
        }

        const d = json.data;
        const sex = d.sex || {};
        const age = d.age || {};
        const ctrb = d.ctrb || {};
        const sido = d.sido || {};
        const sexAge = d.sex_age || {};
        const sexCtrb = d.sex_ctrb || {};
        const sexSido = d.sex_sido || {};

        const ageLabels = Object.keys(age);
        const incomeLabels = Object.keys(ctrb);
        const sidoLabels = Object.keys(sido);

        const maleAge = ageLabels.map(i => Number(sexAge["1"]?.[i] || 0));
        const femaleAge = ageLabels.map(i => Number(sexAge["2"]?.[i] || 0));

        const maleIncome = incomeLabels.map(i => Number(sexCtrb["1"]?.[i] || 0));
        const femaleIncome = incomeLabels.map(i => Number(sexCtrb["2"]?.[i] || 0));

        const maleSido = sidoLabels.map(i => Number(sexSido["1"]?.[i] || 0));
        const femaleSido = sidoLabels.map(i => Number(sexSido["2"]?.[i] || 0));

        sidebarBody.innerHTML = `
                <p><strong>Edge:</strong> ${source} (${sourceLabel}) → ${target} (${targetLabel})    
                <div class="pubmed-button-container">
                    <button id="pubmed-button" onclick="loadPubmed('${source}', '${target}')">관련 논문 보기</button>
                </div>         
                <div class="graph-box"><h4>성별 비율</h4><canvas id="genderEdgeChart"></canvas></div>
                <div class="graph-box"><h4>연령 분포</h4><canvas id="edgeAgeChart"></canvas></div>
                <div class="graph-box"><h4>지역 분포</h4><canvas id="sidoEdgeChart"></canvas></div>
                <div class="graph-box"><h4>소득 수준 분포</h4><canvas id="incomeEdgeChart"></canvas></div>
                <div class="graph-box"><h4>성별 × 연령</h4><canvas id="sexAgeEdgeChart"></canvas></div>
                <div class="graph-box"><h4>성별 × 지역</h4><canvas id="sexSidoEdgeChart"></canvas></div>
                <div class="graph-box"><h4>성별 × 소득</h4><canvas id="sexIncomeEdgeChart"></canvas></div>
            `;

        new Chart(document.getElementById('genderEdgeChart'), {
            type: 'pie',
            data: {
                labels: ['남성', '여성'],
                datasets: [{ data: [sex["1"] || 0, sex["2"] || 0], backgroundColor: ['#4e79a7', '#f28e2b'] }]
            },
            options: { responsive: true }
        });

        new Chart(document.getElementById('edgeAgeChart'), {
            type: 'bar',
            data: {
                labels: ageLabels,
                datasets: [{ label: '연령 분포', data: ageLabels.map(i => age[i]), backgroundColor: '#4e79a7' }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        new Chart(document.getElementById('sexAgeEdgeChart'), {
            type: 'bar',
            data: {
                labels: ageLabels,
                datasets: [
                    { label: '남성', data: maleAge, backgroundColor: '#4e79a7' },
                    { label: '여성', data: femaleAge, backgroundColor: '#f28e2b' }
                ]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        new Chart(document.getElementById('sidoEdgeChart'), {
            type: 'bar',
            data: {
                labels: sidoLabels,
                datasets: [{ label: '지역 분포', data: sidoLabels.map(i => sido[i]), backgroundColor: '#f28e2b' }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        new Chart(document.getElementById('sexSidoEdgeChart'), {
            type: 'bar',
            data: {
                labels: sidoLabels,
                datasets: [
                    { label: '남성', data: maleSido, backgroundColor: '#4e79a7' },
                    { label: '여성', data: femaleSido, backgroundColor: '#f28e2b' }
                ]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        new Chart(document.getElementById('incomeEdgeChart'), {
            type: 'bar',
            data: {
                labels: incomeLabels,
                datasets: [{ label: '소득 분포', data: incomeLabels.map(i => ctrb[i]), backgroundColor: '#59a14f' }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        new Chart(document.getElementById('sexIncomeEdgeChart'), {
            type: 'bar',
            data: {
                labels: incomeLabels,
                datasets: [
                    { label: '남성', data: maleIncome, backgroundColor: '#4e79a7' },
                    { label: '여성', data: femaleIncome, backgroundColor: '#f28e2b' }
                ]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

    })
    .catch(err => {
        console.error("Edge info fetch error:", err);
        sidebarBody.innerHTML = `<p><strong>Edge</strong>: ${source} → ${target}</p><p>정보 불러오기 실패</p>`;
    });
});




cy.on('tap', function (evt) {
    if (evt.target === cy) {
        // 사이드바 닫기
        sidebar.classList.remove("open");

        // 노드 정보 숨기기
        nodeInfo.style.display = "none";

        // PubMed 결과 숨기기
        const resultsDiv = document.getElementById('pubmed-results');
        resultsDiv.style.display = "none";
    }
});

function toggleSidebar() {
    const sidebar = document.getElementById('disease-list');
    sidebar.classList.toggle('show');
}

// 논문 리스트 사이드바
function loadPubmed(sourceId, targetId = null) {
    const slide = document.getElementById("pubmed-slide");
    const body = document.getElementById("pubmed-slide-body");
    slide.classList.add("show");
    body.innerHTML = "<p>논문을 불러오는 중...</p>";

    let url = '';
    if (targetId && sourceId !== targetId) {
        // 엣지: source ≠ target
        url = `/network/search_pubmed/?source=${sourceId}&target=${targetId}`;
    } else {
        // 노드: 단일 질병
        url = `/network/search_pubmed/?code=${sourceId}`;
    }

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.results?.length) {
                body.innerHTML = data.results.map(p => `<p><a href="${p.url}" target="_blank">${p.title}</a></p>`).join('');
            } else {
                body.innerHTML = "<p>관련 논문이 없습니다.</p>";
            }
        })
        .catch(err => {
            console.error("PubMed fetch error:", err);
            body.innerHTML = "<p>논문을 불러오는 중 오류가 발생했습니다.</p>";
        });
}


function closePubmed() {
    document.getElementById("pubmed-slide").classList.remove("show");
}

