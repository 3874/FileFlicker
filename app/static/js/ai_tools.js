async function sendMessageToAI(query, projId) {
    
    try {
        const response = await $.ajax({
            url: '/search/complexSearch',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify([{
                sessionId: projId,
                action: 'sendMessage',
                chatInput: query,
            }]),
            timeout: 40000 
        });
        return response;
    } catch (xhr) {
        if (xhr.statusText === 'timeout') {
            alert('Time Out');
        } else {
            const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : '알 수 없는 오류 발생';
            alert(errorMessage);
        }
    } finally {
        $('#loadingOverlay').hide();
    }
}

async function SearchInFileInVectorDB(query, fileId) {
    
    try {
        const response = await $.ajax({
            url: '/files/fileSearchInVectorDB',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify([{
                fileId: fileId,
                action: 'sendMessage',
                chatInput: query,
            }]),
            timeout: 40000 
        });
        return response;
    } catch (xhr) {
        if (xhr.statusText === 'timeout') {
            alert('Time Out');
        } else {
            const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : '알 수 없는 오류 발생';
            alert(errorMessage);
        }
    } finally {
        $('#loadingOverlay').hide();
    }
}

async function AISearch(chatInput) {
    const url = '/search/AISearch'; // 서버의 엔드포인트 URL
    const data = [{ chatInput }]; // 요청할 데이터 형식에 맞게 배열로 감싸기

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify(data) 
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Error: ${errorData.error}`);
        }

        const result = await response.json(); 
        return result.reply; 

    } catch (error) {
        console.error('Error calling AISearch:', error);
        alert(`Error: ${error.message}`); 
    }
}

async function parseSearchResults(htmlContent, searchEngine) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');

    let targetDivs;
    switch (searchEngine) {
        case 'yahoo':
            targetDivs = doc.querySelectorAll('h3.title.mt-15.mb-4[style="display:block;"]');
            break;
        case 'google':
            targetDivs = doc.querySelectorAll('div.Gx5Zad.xpd.EtOod.pkphOe');
            break;
        default:
            throw new Error('Invalid search engine specified');
    }

    const extractedContent = Array.from(targetDivs).map(element => {
        let link, title, snippet;

        switch (searchEngine) {
            case 'yahoo':
                const linkElementYahoo = element.querySelector('a');
                if (!linkElementYahoo) return null;

                link = linkElementYahoo.getAttribute('href') || '';
                const clonedLinkElementYahoo = linkElementYahoo.cloneNode(true);
                const spansYahoo = clonedLinkElementYahoo.querySelectorAll('span');
                spansYahoo.forEach(span => span.remove());
                title = clonedLinkElementYahoo.textContent.trim();

                const parentDivYahoo = element.closest('div.algo-sr');
                const snippetElementYahoo = parentDivYahoo ? parentDivYahoo.querySelector('.compText.aAbs') : null;
                snippet = snippetElementYahoo ? snippetElementYahoo.textContent.trim() : '';
                break;

            case 'google':
                const linkElementGoogle = element.querySelector('a');
                if (!linkElementGoogle) return null;

                const url = new URL(linkElementGoogle.href);
                link = url.searchParams.get('q') || '';

                const titleElementGoogle = element.querySelector('h3');
                if (titleElementGoogle) {
                    title = titleElementGoogle.textContent.trim();
                    const excludedDiv = element.querySelector('div.egMi0.kCrYT');
                    if (excludedDiv) {
                        excludedDiv.remove();
                    }
                    const snippetDiv = element.querySelector('div.kCrYT');
                    snippet = snippetDiv ? snippetDiv.textContent.trim() : '';
                }
                break;
        }

        return link && title ? { link, title, snippet } : null;
    }).filter(item => item !== null);

    return extractedContent; 
}

async function extractContent(url) {
    const allOriginsUrl = 'https://api.allorigins.win/get?url=' + url;

    try {
        const response = await fetch(allOriginsUrl, {
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
            }
        });
        const data = await response.json();

        if (data.contents) {
            return data.contents;
        } else {
            throw new Error('No contents');
        }
    } catch (error) {
        console.error('에러 발생:', error);
        return null;
    }
}

async function searchDuckDuckGo(query) {
    const apiUrl = "https://api.duckduckgo.com/";
    const url = `${apiUrl}?q=${encodeURIComponent(query)}&format=json`;
  
    await $.ajax({
      url: url,
      type: 'GET', 
      dataType: 'json', 
      success: function(data) {
        console.log("검색 결과:", data);
  
        if (data.Answer) {
          console.log("Reply:", data.Answer);
        } else if (data.Abstract) {
          console.log("Abstract:", data.Abstract);
        } else {
          console.log("No reply found");
        }
      },
      error: function(xhr, status, error) {
        console.error("Error fetching DuckDuckGo API:", error);
      }
    });
  }
