# -*- coding: utf-8 -*-
# This file is a part of 'spinxcontrib.inlineparams' project, which is an HTML
# postprocessor to achieve parameter list flat design. See sphinx/index.rst for
# more information.
#
# Copyright (c) 2015 Pavel Kretov.
# Provided under the terms of MIT license.
import sys
import re
import bs4


def tweak_parameter_item(item, soup):
    # Parameter 'item' may refer to either <li> or <p class="first last"> tag.
    # The latter case means that it's the only one list item, reduced by Sphinx
    # to single paragraph. If so, expand <p> back to <ul><li>...</li></ul>.
    if item.name == "p":
        item.name = "li"
        item["class"] = "inline-params-par-item"
        item.wrap(soup.new_tag("ul"))

    # Create regular expressions only once.
    re_opening_paren = re.compile("^\\s*\\(")
    re_closing_paren = re.compile("^\\s*\\) – ", re.M)

    # Now 'item' should look like the following HTML code:
    #     <li><strong>param</strong> (<em>type</em>) – Description ... </li>
    #
    # which is going to unpack into the list:
    #     [<strong>param</strong>, ' (', <em>type</em>, ') – Description ... ']
    #
    if len(item.contents) <= 3:
        return

    strong, paren_op, em, paren_cl, *paren_rest = item.contents
    looks_fine = (isinstance(strong,   bs4.Tag)    and
                  isinstance(em,       bs4.Tag)    and
                  isinstance(paren_op, str)        and
                  isinstance(paren_cl, str)        and
                  strong.name == "strong"          and
                  em.name     == "em"              and
                  re_opening_paren.match(paren_op) and
                  re_closing_paren.match(paren_cl))

    if looks_fine:
        return

    paren_op.replace_with(": ")
    paren_cl.insert_before(soup.new_tag("br"))
    paren_cl.replace_with(re_closing_paren.sub(paren_cl, ""))


def tweak_html_dom(soup):

    tables = soup.find_all("table", class_=["docutils","field-list"])
    for table in tables:
        ths = table.find_all("th", class_="field-name")
        tds = table.find_all("td", class_="field-body")

        #
        replacement = soup.new_tag("div", class_="inline-params")
        for th, td in zip(ths, tds):
            print("TH=", th)
            print("TD=", td)

            #
            header = th.extract()
            header.name = "div"
            header["class"] = "inline-params-header"

            #
            paramlist = td.extract()
            paramlist.name = "div"
            paramlist["class"] = "inline-params-parameters"

            for p in paramlist.findChildren("li"):
                tweak_parameter_item(p, soup)

            for p in paramlist.findChildren("p", class_=["first", "last"]):
                tweak_parameter_item(p, soup)

            #
            replacement.contents.append(header)
            replacement.contents.append(paramlist)

        table.insert_before(replacement)
        table.decompose()


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        soup = bs4.BeautifulSoup(f.read(), "html.parser")

    tweak_html_dom(soup)

    with open(sys.argv[1]+".mod.html",mode='w') as f:
        f.write(soup.prettify())