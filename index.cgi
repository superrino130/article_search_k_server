#!C:/Ruby27-x64/bin/ruby
print "Content-type: text/html; charset=iso-8859-1\n\n"

require 'cgi'
require 'bio'
require 'mechanize'
require 'date'

def jpost_rev(id, rev)
  "https://repository.jpostdb.org/xml/" + id + ".#{rev}.xml"
end

def get_jpost(id)
  begin
    id = 'JPST' + format("%06d", id.to_s.chomp)
  rescue => exception
    return
  end
  @jpost_info[:id] = id
  @agent = Mechanize.new
  @agent.user_agent_alias = 'Windows Mozilla'
  page = ''
  f = false
  20.times do |rev|
    if @agent.get(jpost_rev(id, rev)).search('title')[0].to_s.include?('jPOSTrepo')
      if f
        break
      else
        next
      end
    end
    page = @agent.get(jpost_rev(id, rev))
    f = true
    sleep 0.1
  end

  begin
    s = page.search('Project').to_s
  rescue => exception
    return
  end
  return if s.empty?
  @jpost_info[:pxid] = s[s.index('PXD'), 9] if s.index('PXD')
  @jpost_info[:createdDate] = s[s.index('createdDate') + 13, 10]
  @jpost_info[:keywords] = page.search('Keywords').to_s.gsub('<Keywords>', '').gsub('</Keywords>', '')
  if @jpost_info[:keywords].include?(';')
    @jpost_info[:keywords] = @jpost_info[:keywords].split(';').map{ _1.strip }
  elsif @jpost_info[:keywords].include?(',')
    @jpost_info[:keywords] = @jpost_info[:keywords].split(',').map{ _1.strip }
  else
    @jpost_info[:keywords] = @jpost_info[:keywords].split().map{ _1.strip }
  end
  s = page.search('Contact')
  @jpost_info[:pi] = s.search('PrincipalInvestigator').to_s.gsub('<PrincipalInvestigator>', '').gsub('</PrincipalInvestigator>', '')
  if @jpost_info[:pi].nil?.!
    @jpost_info[:pi] = @jpost_info[:pi].gsub(/[^\w]*(Dr|MD|PhD|Prof)[^\w]*/, '')
  end
  @jpost_info[:pi] = '' if @jpost_info[:pi].upcase == @jpost_info[:pi].downcase
  @jpost_info[:pi] += '[AU]' if @jpost_info[:pi] != ''
  @jpost_info[:sm] = s.search('Name').to_s.gsub('<Name>', '').gsub('</Name>', '')
  if @jpost_info[:sm].nil?.!
    @jpost_info[:sm] = @jpost_info[:sm].gsub(/[^\w]*(Dr|MD|PhD|Prof)[^\w]*/, '')
  end
  @jpost_info[:sm] = '' if @jpost_info[:sm].upcase == @jpost_info[:sm].downcase  
  @jpost_info[:sm] += '[AU]' if @jpost_info[:sm] != ''
end

def google_scholar(jpst)
  @google_scholar = { url: nil, anchor: [] }
  return if jpst.nil?
  url = "https://scholar.google.com/scholar?hl=ja&q=" + jpst
  url << "+OR+" << @jpost_info[:pxid] if @jpost_info[:pxid].nil?.!
  @google_scholar[:url] = url
  
  anchor_pdf = []
  anchor_pdf2 = []
  anchor_pmc = []
  anchor_full = []
  anchor_else = []
  begin
    page = @agent.get(url)    
  rescue => exception
    @google_scholar[:anchor] = ["errorが発生しましたので、上のgoogle scholarのリンクを開いてください"]
    return
  end
  page.search('a').each do |anchor|
    next if anchor[:href].include?('javascript') || anchor[:href].include?('google') || anchor[:href][0] == '/' || anchor[:href].include?('https://scholar')
    if anchor[:href][-3, 3].upcase == 'PDF'
      anchor_pdf << anchor[:href]
    elsif anchor[:href].upcase.include?('PDF')
      anchor_pdf2 << anchor[:href]
    elsif anchor[:href].include?('https://www.ncbi.nlm.nih.gov/pmc/')
      anchor_pmc << anchor[:href]
    elsif anchor[:href].upcase.include?('FULL')
      anchor_pdf2 << anchor[:href]
    else
      anchor_else << anchor[:href]
    end
  end
  @google_scholar[:anchor] = anchor_pdf + anchor_pdf2 + anchor_pmc + anchor_full + anchor_else
end

def pubmed_search()
  return if @jpost_info[:createdDate].nil?
  sdate = Date.parse(@jpost_info[:createdDate][0, 8] + '01')
  
  @pubmed_id[:maxdate] = sdate.next_month(13).strftime("%Y/%m/%d")
  @pubmed_id[:mindate] = sdate.prev_month.strftime("%Y/%m/%d")
  @ids = Hash.new(0)

  options = {
    'maxdate' => @pubmed_id[:maxdate],
    'mindate' => @pubmed_id[:mindate],
    'retmax' => 1000
  }

  if @jpost_info[:pi] != ''
    Bio::PubMed.esearch(@jpost_info[:pi], options).each do |x|
      @ids[x] += 1
    end
    sleep 0.5
  end
  if @jpost_info[:sm] != '' && @jpost_info[:pi] != @jpost_info[:sm]
    Bio::PubMed.esearch(@jpost_info[:sm], options).each do |x|
      @ids[x] += 2
    end
    sleep 0.5
  end
  @ids = @ids.sort_by{ _1 }[0...100]
  @pubmed_id[:size] = @ids.size
  @ids.each do |k, v|
    @ids[k] = keywords_count(k, v)
    sleep 0.5
  end
  @ids.sort_by{ -_2.size }.each do |k, v|
    @ids.delete(k) if v.size == 1 && v != ['pi+sm']
  end
end

def keywords_count(id, v)
  bibinfo = Bio::PubMed.efetch(id)
  medlines = bibinfo.map{ Bio::MEDLINE.new(_1) }
  s = ''
  a = []
  if v == 1
    a << 'pi'
  elsif v == 2
    a << 'sm'
  elsif v == 3
    a << 'pi+sm'
  end
  medlines.each do |x|
    s = x.ab.upcase  # abstract
  end
  @jpost_info[:keywords].each do |x|
    if s.include?(x.upcase)
      a << x
    end
  end
  a
end

def main()
  textbox = CGI.new
  id = textbox['inputedid']
  print <<-EOF
  <html><title>article search CGI</title>
  <body bgcolor='#faebd7'>
  <div class="user_form">
    <form action="index.cgi" method = "post">
      <span>input jPOST id (ex. JPST000855 => 855)</span><br>
      <input type="text" name="inputedid" class="user_input_box">
      <input type="submit" value="search" class="btn btn_user">
    </form>
  </div>
  EOF
  if id.size > 0
    @jpost_info = {}
    get_jpost(id)
    puts "----- jPOST info -----<br>"
    puts "<a href='https://repository.jpostdb.org/entry/#{@jpost_info[:id]}' target='_blank' rel='noopener noreferrer'>#{@jpost_info[:id]}</a> #{@jpost_info[:pxid]} createdDate: #{@jpost_info[:createdDate]}<br>"
    puts "pi: #{@jpost_info[:pi]}" if @jpost_info[:pi]
    puts "sm: #{@jpost_info[:sm]}" if @jpost_info[:sm]
    puts "<br>"
    puts "[ " + @jpost_info[:keywords].join(', ') + " ]" if @jpost_info[:keywords]
    puts "<p>"
    if @jpost_info[:createdDate]
      google_scholar(@jpost_info[:id])
      puts "--- google scholar ---<br>"
      puts "<a href=#{@google_scholar[:url]} target='_blank' rel='noopener noreferrer'>#{@google_scholar[:url]}</a><br><br>"
      @google_scholar[:anchor].each do |anchor|
        puts "<a href=#{anchor} target='_blank' rel='noopener noreferrer'>#{anchor}</a><br>"
      end
      puts "<p>"
      puts "------- PubMed -------<br>"
      @pubmed_id = {}
      begin
        pubmed_search()
        puts "from #{@pubmed_id[:mindate]} to #{@pubmed_id[:maxdate]}<br>"
        puts "#{@pubmed_id[:size]} papers hit<br>"
        if @pubmed_id[:size] && @pubmed_id[:size] < 100
          if @ids
            @ids.sort_by{ -_2.size }.each do |k, v|
              puts "<a href='http://www.ncbi.nlm.nih.gov/pubmed/' + #{k} target='_blank' rel='noopener noreferrer'>#{k}</a><br>"
              puts "#{v}<br>"
            end
          end
        end
      rescue => exception
        # PASS
      end
    end
  end
  print <<-EOE
  </body>
  </html>
  EOE
end

main()
