var app = new Vue({
    el: '#app',
    data: {
        title: '人民日报 00 至 15 年的新闻',
        searchButtonText: '搜索',
        docs: [],
        query: null,
        sortOrder: 'desc',
        searchResultStat: null, // 用于显示搜索结果的统计信息
        searchStartTime: null,  // 用于计算查询耗时

        curPage: 1,
        pageSize: 10,
        pageCount: 1,

        API_SEARCH: "http://127.0.0.1:5000/search",
    },
    methods: {
        updatePageNav() {
            // Update visibility
            if (this.docs == null || this.docs.length == 0) {
                this.setClassVisible('.page-nav-container', false);
                this.setClassVisible('.page-nav-prev', false);
                this.setClassVisible('.page-nav-next', false);
            } else {
                this.setClassVisible('.page-nav-container', true);
                this.setClassVisible('.page-nav-prev', this.curPage > 1);
                this.setClassVisible('.page-nav-next', this.curPage < this.pageCount);
            }

            // Update current page input
            let curPageInputs = document.getElementsByClassName('cur-page-input');
            for (let i = 0; i < curPageInputs.length; i++) {
                curPageInputs[i].value = this.curPage;
            }
        },
        setClassVisible(name, visible) {
            // Set visibility of all elements in a class.
            let s = visible ? 'visible' : 'hidden';
            let prevPage = document.querySelectorAll(name);
            for (let i = 0; i < prevPage.length; i++) {
                prevPage[i].style.visibility = s;
            }
        },
        setElementVisible(name, visible) {
            // Set visibility of one element.
            // Return null if input is invalid.
            let elem = document.querySelector(name);
            elem.style.visibility = visible ? 'visible' : 'hidden';
        },
        isDateValid(year, month, day) {
            // Check if a date is valid.
            // Return true if valid, false otherwise.
            console.log(year, month, day);
            year = Number(year);
            month = Number(month);
            day = Number(day);
            console.log(year, month, day);
            if (isNaN(year) || year.length < 0 || year > 9999) {
                return false;
            }
            if (isNaN(month) || month < 1 || month > 12) {
                return false;
            }
            if (isNaN(day) || day < 1 || day > 31) {
                return false;
            }
            return true;
        },
        getMinDate() {
            // Get the min date from filter input.
            // Return null if input is invalid.
            let yearInput = document.querySelector('#filter-time-start-input-year').value;
            let monthInput = document.querySelector('#filter-time-start-input-month').value;
            let dayInput = document.querySelector('#filter-time-start-input-day').value;
            if (!this.isDateValid(yearInput, monthInput, dayInput)) {
                return null;
            }
            let year = yearInput.padStart(4, '0');
            let month = monthInput.padStart(2, '0');
            let day = dayInput.padStart(2, '0');
            return year + '-' + month + '-' + day;
        },
        getMaxDate() {
            // Get the max date from filter input
            let yearInput = document.querySelector('#filter-time-stop-input-year').value;
            let monthInput = document.querySelector('#filter-time-stop-input-month').value;
            let dayInput = document.querySelector('#filter-time-stop-input-day').value;
            if (!this.isDateValid(yearInput, monthInput, dayInput)) {
                return null;
            }
            let year = yearInput.padStart(4, '0');
            let month = monthInput.padStart(2, '0');
            let day = dayInput.padStart(2, '0');
            return year + '-' + month + '-' + day;
        },
        onInvalidDate() {
            // Make input red when it is invalid
            let inputs = document.querySelectorAll('.filter-time-start-input, .filter-time-stop-input');
            for (let input of inputs) {
                // inputs[i].classList.add('is-invalid');
                input.style.backgroundColor = "#ff8888";
            }
        },
        onValidDate() {
            // Make input normal when it is valid
            let inputs = document.querySelectorAll('.filter-time-start-input, .filter-time-stop-input');
            for (let input of inputs) {
                // inputs[i].classList.remove('is-invalid');
                input.style.backgroundColor = "white";
            } 
        },
        getDocs() {
            // Get documents from data using current data in `this`.
            if (this.query == null) {
                return;
            }

            let url = this.API_SEARCH + '?query=' + this.query;
            let minIdx = (this.curPage - 1) * this.pageSize;
            let maxIdx = minIdx + this.pageSize;
            url += '&min_index=' + minIdx.toString();
            url += '&max_index=' + maxIdx.toString();
            url += '&sort_order=' + this.sortOrder;
            let minDate = this.getMinDate();
            let maxDate = this.getMaxDate();
            if (minDate == null || maxDate == null) {
                this.onInvalidDate();
                return;
            } else {
                this.onValidDate();
            }
            url += '&min_date=' + minDate;
            url += '&max_date=' + maxDate;

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
            console.log("GET", url);
            let self = this; // `this` is not available in the callback function.

            this.searchStartTime = new Date();

            // Make the request.
            axios.get(url, body)
                .then(function (response) {
                    self.onGotDocs(response.data);
                })
                .catch(function (error) {
                    console.log("error", error);
                });
        },
        onPrevPage() {
            if (this.curPage > 1) {
                this.curPage -= 1;
                this.getDocs();

            }
            this.updatePageNav();
        },
        onNextPage() {
            if (this.curPage < this.pageCount) {
                this.curPage += 1;
                this.getDocs();
            }
            this.updatePageNav();
        },
        onGotDocs(result) {
            // Triggered when successfully fetched documents from database.
            console.log('onGotDocs');

            // Restore search bar color.
            let queryInput = document.querySelector('#search-bar');
            queryInput.style.backgroundColor = 'white';
            // console.log(result);

            // Calculate time spent querying
            let elapsed_time = (new Date() - this.searchStartTime) / 1000;

            this.docs = [];
            let docs = result.docs;
            let total = result.total;
            this.pageCount = Math.ceil(total / this.pageSize);

            if (result.status == 'error') {
                console.log('error', result);
                if (result.message == "invalid query") {
                    this.onInvalidQuery(result.message);
                } else {
                    this.onGetDocsError(result.message);
                }
            } else if (total == 0) {
                // If no results found, show no result text.
                this.setElementVisible('#no-result-text', true);
            } else {
                // Parse and add documents to `this.docs`.
                function tokensNestedArrayToString(content) {
                    text = "";
                    for (let pi in content) {
                        let para = content[pi];
                        for (let si in para) {
                            sent = para[si];
                            text += sent.join('');
                        }
                        text += "\n\n";
                    }
                    return text;
                }
                function parseDate(s) {
                    // Parse date string, yyyy-mm-dd into yyyy年mm月dd日
                    let year = parseInt(s.substring(0, 4));
                    let month = parseInt(s.substring(5, 7));
                    let day = parseInt(s.substring(8, 10));
                    return `${year}年${month}月${day}日`;
                }
                for (let i in docs) {
                    // Concatenate tokens in `content` into a single string, where each
                    // paragraph is separated by two newlines (one blank line).
                    let doc = docs[i];
                    doc.content = tokensNestedArrayToString(doc.content);
                    doc.date = parseDate(doc.date);
                    this.docs.push(doc);
                }
                this.setElementVisible('#no-result-text', false);
            }

            this.updatePageNav();
            this.searchResultStat = `${docs.length} 个结果（总：${total}）耗时 ${elapsed_time} 秒`
        },
        onSearch() {
            // Execute search, fetch documents from database.
            this.query = document.getElementById('search-bar').value;
            this.curPage = 1;
            this.getDocs();
        },
        onInputCurPage() {
            let curPageInputs = document.querySelectorAll('.cur-page-input');
            let curPage = parseInt(curPageInputs[0].value);
            if (isNaN(curPage) || curPage < 1 || curPage > this.pageCount) {
                curPageInputs[0].value = this.curPage;
            } else {
                this.curPage = curPage;
                this.getDocs();
            }
        },
        onClickSortOrder() {
            // Change sort order, will redo a search and go to page 1.
            let button = document.querySelector('#sort-order-button');
            if (button.textContent == '升序') {
                button.textContent = '降序';
                this.sortOrder = 'desc';
            } else {
                button.textContent = '升序';
                this.sortOrder = 'asc';
            }
            this.onSearch();
        },
        highlight(contentStr) {
            // Highlight all occurences of query tokens in `contentStr` by
            // inserting a HTML span.

            // Get all tokens in query, remove operators
            let query = this.query.toLowerCase();
            let toRemove = ['and', 'or', 'not', '(', ')', '（', '）'];
            for (let i in toRemove) {
                query = query.replaceAll(toRemove[i], ' ');
            }
            // Make sure there are not contiguous spaces.
            query = query.replace(/\s+/g, ' ').trim();
            let tokens = query.split(' ');
            for (let i in tokens) {
                token = tokens[i];
                let highlightedToken = '<span class="highlighted">' + token + '</span>'
                contentStr = contentStr.replaceAll(token, highlightedToken);
            }
            return contentStr;
        },
        onInvalidQuery(message) {
            // Triggered when query is invalid.
            console.log('onInvalidQuery');
            console.log(message);
            this.docs = [];
            let queryInput = document.querySelector('#search-bar');
            queryInput.style.backgroundColor = '#ffcccc';
            this.searchResultStat = message;
            this.setElementVisible('#no-result-text', false);
            this.updatePageNav();
        },
        onGetDocsError(message) {
            // Triggered when error occurs while fetching documents from database.
            console.log('onGetDocsError');
            console.log(message);
            this.docs = [];
            this.searchResultStat = message;
            this.setElementVisible('#no-result-text', false);
            this.updatePageNav();
        },
    }
})