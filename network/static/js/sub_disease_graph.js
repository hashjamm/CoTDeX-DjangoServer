// 다중 질병 그래프 전용 JavaScript
document.addEventListener("DOMContentLoaded", function () {
    console.log("📌 Sub Disease Graph DOMContentLoaded - 페이지 로드됨");
    
    // 노드 목록 업데이트 함수
    window.updateNodeList = function(nodeNames) {
        const nodeListElement = document.getElementById("node-list");
        if (!nodeListElement) return;
        
        nodeListElement.innerHTML = "";
        nodeNames.forEach(name => {
            const li = document.createElement("li");
            li.textContent = name;
            li.style.padding = "5px";
            li.style.borderBottom = "1px solid #eee";
            nodeListElement.appendChild(li);
        });
    };

    // Follow-Up 값 업데이트 함수
    window.updateFollowUpValue = function (val) {
        const followUpText = document.getElementById("follow-up-text");
        if (followUpText) {
            followUpText.innerText = val;
        }
    };

    // 그래프 업데이트 함수
    window.updateGraph = function() {
        const selectedDiseases = window.graphData.selected_codes;
        const followUp = document.getElementById("follow-up-slider").value;
        const rrMin = document.getElementById("rr-min").value;
        const rrMax = document.getElementById("rr-max").value;
        const chisq = document.getElementById("chisq-p").value;
        const fisher = document.getElementById("fisher-p").value;

        fetch(`/network/sub_disease_graph/?diseases=${selectedDiseases}&follow_up=${followUp}&rr_values_min=${rrMin}&rr_values_max=${rrMax}&chisq_p_values=${chisq}&fisher_p_values=${fisher}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert("❌ 오류: " + data.error);
                return;
            }
            
            // 기존 요소 제거
            cy.elements().remove();
            
            // 새 요소 추가
            cy.add(data.nodes);
            cy.add(data.edges);
            
            // 레이아웃 실행
            cy.layout({
                name: 'fcose',
                animate: true,
                fit: true,
                padding: 30,
                nodeDimensionsIncludeLabels: true,
                nodeRepulsion: 150000,
                uniformNodeDimensions: false,
                idealEdgeLength: 300,
                edgeElasticity: 0.2,
                gravity: 1.5,
                gravityRangeCompound: 2.0,
                gravityCompound: 2.0,
                nestingFactor: 0.8,
                tile: true,
                randomize: true,
                quality: "proof",
                numIter: 8000
            }).run();
            
            // 노드 목록 업데이트
            if (data.node_names) {
                updateNodeList(data.node_names);
            }
        })
        .catch(err => {
            console.error("❌ 그래프 데이터 오류:", err);
        });
    };

    // 사이드바 토글 함수
    window.toggleSidebar = function() {
        const sidebar = document.getElementById('disease-list');
        if (sidebar) {
            sidebar.classList.toggle('show');
        }
    };

    // PubMed 관련 함수들
    window.loadPubmed = function(sourceId, targetId = null) {
        const slide = document.getElementById("pubmed-slide");
        const body = document.getElementById("pubmed-slide-body");
        
        if (slide && body) {
            slide.classList.add("show");
            body.innerHTML = "<p>논문을 불러오는 중...</p>";
            
            let url = '';
            if (targetId && sourceId !== targetId) {
                url = `/network/search_pubmed/?source=${sourceId}&target=${targetId}`;
            } else {
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
    };

    window.closePubmed = function() {
        const slide = document.getElementById("pubmed-slide");
        if (slide) {
            slide.classList.remove("show");
        }
    };

    // 초기 노드 목록 설정
    if (window.graphData.node_names) {
        updateNodeList(window.graphData.node_names);
    }
}); 