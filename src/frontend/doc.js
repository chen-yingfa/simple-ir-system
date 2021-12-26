var app = new Vue({
    el: '#app',
    data: {
        title: '人民日报 00 至 15 年的新闻',
        docs: [],

        API_SEARCH: "http://127.0.0.1:5000/search",
		API_GET_DOC: "http://127.0.0.1:5000/get_doc",
		API_GET_SIMILAR_DOCS: "http://127.0.0.1:5000/get_similar_docs",
		readingDoc: {
			title: '一个标题',
			content: '一些内容',
			date: '2018-01-01',
			author: '陈英发',
			column: '一条栏目',
			file_name: '一个文件',
		}
    },
    methods: {
        setClassVisible(name, visible) {
            // Set visibility of all elements in a class.
            let s = visible ? 'visible' : 'hidden';
            let elems = document.querySelectorAll(name);
			console.log(elems);
            for (let i = 0; i < elems.length; i++) {
                elems[i].style.visibility = s;
            }
        },
        setElementVisible(name, visible) {
            // Set visibility of one element.
            // Return null if input is invalid.
            let elem = document.querySelector(name);
            elem.style.visibility = visible ? 'visible' : 'hidden';
        },
        onClickDocItem(event) {
            console.log("onClickDocItem()");
            let clicked = event.target.closest('.doc-item');
            let docId = clicked.getAttribute('doc-id');
            console.log('docId', docId);
            
            params = new URLSearchParams();
            params.append('docId', docId);
            let targetUrl = `./doc.html?${params.toString()}`;
            location.href = targetUrl;
        },
		onExit() {
			location.href = './index.html';
		},
		apiGet(url, callback) {
            body = {
                type: "GET",
                data: {},
                datatype: "json",
                xhrFields: {
                    withCredentials: true,
                },
                crossDomain: true,
                contentType: 'application/json; charset=utf-8',
            }
            // Make the request.
            axios.get(url, body)
                .then(function (response) {
                    callback(response.data);
                })
                .catch(function (error) {
                    console.log("error", error);
                });

		},
		getDocById(docId, callback) {
            let url = this.API_GET_DOC + '?doc_id=' + docId;
			this.apiGet(url, callback);
		},
		parseDate(s) {
			// Parse date string, yyyy-mm-dd into yyyy年mm月dd日
			let year = parseInt(s.substring(0, 4));
			let month = parseInt(s.substring(5, 7));
			let day = parseInt(s.substring(8, 10));
			return `${year}年${month}月${day}日`;
		},
		parseContent(content, maxLen=null, maxParaCnt=null, paraPrefix='', paraSuffix='\n\n') {
			let text = "";
			let paraCnt = 0;
			for (let pi in content) {
				let para = content[pi];
				let paraStr = ''
				for (let si in para) {
					sent = para[si];
					paraStr += sent.join('');
				}
				if (paraStr.length == 0) continue; // Skip empty paragraph.
				paraCnt++;
				if (maxParaCnt && paraCnt > maxParaCnt) break;
				text += paraPrefix + paraStr + paraSuffix;
			}
			text = text.trimEnd();
			if (maxLen) {
				if (text.length > maxLen) {
					text = text.substring(0, maxLen).trimEnd();
					text += "……";
				}
			}

			return text;
		},
		getReadingDoc() {
			console.log('getReadingDoc');
			let docId = this.getDocId();
			console.log("docId: " + docId);

			let self = this;  // This can't be accessed in nested function.
			function onGotReadingDoc(data) {
				self.readingDoc = data.doc;
				self.readingDoc.date = self.parseDate(self.readingDoc.date);
				self.readingDoc.content = self.parseContent(self.readingDoc.content);
			}

			this.getDocById(docId, onGotReadingDoc);
		},
		getSimilarDocs() {
			let docId = this.getDocId();
			console.log("docId: " + docId);

			let self = this;
			function onGotSimilarDocs(data) {
				self.docs = data.docs;
				for (let i in data.docs) {
					let content = data.docs[i].content;
					self.docs[i].content = self.parseContent(content, 240, 8, '    ', '\n');
				}
				console.log("Hiding loading-suggestion-container");
				self.setClassVisible(".loading-suggestion-container", false);
			}
			let url = this.API_GET_SIMILAR_DOCS + '?doc_id=' + docId;
			this.apiGet(url, onGotSimilarDocs);
		},
		getDocId() {
			let params = new URLSearchParams(window.location.search);
			let docId = params.get('docId');
			return docId;
		}
    },
	mounted() {
		this.setClassVisible(".loading-suggestion-container", true);		
		this.getReadingDoc();
		this.getSimilarDocs();
	}
})