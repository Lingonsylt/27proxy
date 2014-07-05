var addCell = function(to, from, num, caption, bar) {
    console.log(from.find("td:nth-child(" + num + ")"));
    to.append('<span>' + caption + '</span> ' +
        from.find("td:nth-child(" + num + ")").text() + '<span>' + bar + '</span>');
};

$(document).ready(function() {
    $(".navigation").off();
    $(".navigation").unbind();
    window.scrollMonitor = null;

    $(".topobox").each(function() {
        var tpbox = $(this);
        var canvas = tpbox.find("canvas");
        var canvas_width = canvas.width();

        tpbox.find(".nbr").each(function() {
            var jq_elem = $(this);
            jq_elem.data("orig-left", jq_elem.css('left'));
            jq_elem.data("orig-top", jq_elem.css('top'));
        });

        var updateNBRPositions = function() {
            var new_canvas_width = canvas.width();
            var ratio = new_canvas_width / canvas_width;
            tpbox.find(".nbr").each(function() {
                var jq_elem = $(this);
                var orig_left = parseInt(jq_elem.data('orig-left'), 10);
                jq_elem.css("left", Math.round(orig_left * ratio) + "px");
                var orig_top = parseInt(jq_elem.data('orig-top'), 10);
                jq_elem.css("top", Math.round(orig_top * ratio) + "px");
            });
        };

        $(window).resize(updateNBRPositions);
    });

    $("head").append("\
        <style type='text/css'> \
        @media screen and (max-width: 600px) { \
            .topobox { \
                width: 100% !important; \
            } \
            \
            .topobox { \
                height: auto !important; \
            } \
            \
            .topobox img { \
                width: 100% !important; \
                height: auto !important; \
            } \
            \
            .topobox canvas { \
                width: 100%; \
            } \
        } \
        </style>");

    $(".topobox").resize();

    $("table.crags th:last-child").after("<th>+</th>");
    $("table.crags tr").each(function() {
        var tr = $(this);
        var plus = $('<td><a href="#">+</a></td>').insertAfter($(this).find("td:last-child"));

        var plusHandler = function(evt) {
            var target  = $(evt.target);
            if( target.is('a') && target.attr("href") != "#") {
                return true;
            }
            evt.preventDefault();
            plus.hide();
            var new_tr = $('<tr><td class="foldout" colspan="5"></td>').
                insertAfter(tr);
            var new_td = new_tr.find("td");
            addCell(new_td, tr, 3, '<span class="stars"><div class="star full"></div></span>',
                " &nbsp; ");
            addCell(new_td, tr, 4, "Routes:", " &nbsp; ");
            addCell(new_td, tr, 8, "Trad:", " &nbsp; ");
            addCell(new_td, tr, 10, "Topos:", " &nbsp; ");
            addCell(new_td, tr, 5, "under 5+:", " &nbsp; ");
            addCell(new_td, tr, 6, "6a-6c:", " &nbsp; ");
            addCell(new_td, tr, 6, "6c+-7b:", " &nbsp; ");
            addCell(new_td, tr, 6, "7b+ over:", "");

            var minus = $('<td><a href="#">-</a></td>').appendTo(tr);
            tr.off('click');

            tr.click(function(evt) {
                var target  = $(evt.target);
                if( target.is('a') && target.attr("href") != "#") {
                    return true;
                }
                evt.preventDefault();
                plus.show();
                new_tr.remove();
                tr.click(plusHandler);
                minus.remove();
            });
        };

        tr.click(plusHandler);
    });
});