# Ruby 3.2 removed File.exists?. jekyll-paginate-content 1.1.0 (latest release)
# still calls it in generator-cache.rb, which breaks every `jekyll serve`
# regeneration after the first build. Remove once the gem ships a fix.
class File
  class << self
    alias exists? exist? unless respond_to?(:exists?)
  end
end
